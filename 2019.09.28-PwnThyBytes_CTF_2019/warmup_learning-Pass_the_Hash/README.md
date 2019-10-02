## Warmup/Learning - Pass the Hash

Server-side script does following:

* Generates 20-byte random password.
* Asks user for 24-byte salt, then generates hash based on previously
generated password and user-provided hash and sends that hash back to user. In
loop, up to 1024 times.
* Sends randomly generated salt to user and asks user to provide correct hash
for that salt and previously generated password.
* Sends the flag if user-provided hash is correct.

The right direction was determined almost immediately after reading the script:
sending specially crafted(?) salts multiple times and examining the
resulting hashes should somehow help to deduce the random password.

After further examination of script I noticed few weird things about the
`combo_hash()`:

* It uses salt value between the two copies of password as initial value for
hash: `salted_pass = password + salt + password`.
* On each round, it splits result of the previous round (or `salted_pass` on
first) and uses some "normal" hash algorithm on both halves separately.
* On each round, it uses XOR on result of the previous round (or `salted_pass`
on first) and calculated "normal" hashes to produce the new value.

To better see what really happens here, we could write this as follows:

```
spl, spr - left and right parts of the initial salted_pass
h(v) - generates hash based on value v
r - final result of all rounds

round 0) r = spl ^ h(spr)                   + spr ^ h(spl)
round 1) r = spl ^ h(spr) ^ h(spr ^ h(spl)) + spr ^ h(spl) ^ h(spl ^ h(spr))
...
```

which could be simplified to:

```
rnd(v) - generates some pseudo-random text based on seed v
rnd(v)[l], rnd(v)[r] - left and right halves of pseudo-random text

r = spl ^ rnd(salted_pass)[l] + spr ^ rnd(salted_pass)[r]
```

So far, we have following:

* Obviously, XOR can be reversed by XORing again with the same value.
* We know last 12 bytes of `spl` and first 12 bytes of `spr` because we provide
them as a salt.

Based on this, we are already able to recover some part of `rnd(salted_pass)`.
But this is useless for recovering the random password because completely
different parts of `rnd(salted_pass)` are XORed with parts of `salted_pass`
containing password. But are they really different?

I tried to carefully read `xor()` function again and realized that if the first
argument (`spl` or `spr`) is longer than the second argument (`h(v)`), it
actually starts reusing some bytes from the second argument! Half of the
`salted_pass` is 32 bytes, but three of four "normal" hashes has only 20 byte
result. This means that, with some probability, script generates final hash
where `rnd(salted_pass)` contains repeating sequences. And thus, with some
probability, we are able to recover the password.

The simplified brute-force algorithm is:

* Feed server with completely random salt values.
* Un-XOR parts of `rnd(salted_pass)` based on known random salt.
* Assume that we are lucky and only 20 bytes of each half of `rnd(salted_pass)`
are actually unique. Try to un-XOR parts of the initial random password.
* If we've got the same value two times from different iterations, then this is
the real password.

The rest is simple: terminate guessing cycle, calculate hash based on server's
salt and on recovered password, send calculated hash back to server.

Code is [here](./solution.py).
