## Challenge: verifier

Challenge is an interactive shell accessible via TCP/IP using `netcat`.
`SyntaxError` after any random input gives as a clue that shell expects some
particular input, maybe commands. Obvious `?`, `help` and `h` have no effect
(same `SyntaxError`).

Fortunately, [source code](./challenge/) in Python is also given to us.

### Source code

Quick look at the source code shows us that service implements an interpreter
for a simple expression language. It uses
[PLY (Python Lex-Yacc)](http://www.dabeaz.com/ply/) as a lexer/parser library.

[lexer.py](./challenge/lexer.py) and [parser.py](./challenge/parser.py) reveals
that implemented language supports following:

 * variable names (and assignment using `=`);
 * integer literals (bots positive and negative);
 * usual binary operations: `+`, `-`, `*`;
 * comparisons: `==`, `<`, `<=`, etc.;
 * "if/else":
`<condition (comparison)> ? { <code on true> } : { <code on false> }`;
 * "while" loop: `[<condition (comparison)> { <code while true> }]`;
 * "print" command: `!<expression>`;
 * "get random number from interval" expression: `<from int> ~ <to int>`;
 * semicolon for command sequences.

Maybe I missed some other constructions.

Anyway, this is enough to write simple programs:

```
> a=123;!a
123

> i=10;[i>0{i=i-(1);x=1~4;!x}]
2
3
1
4
4
1
1
2
3
1
```

But where is the flag?

```
$ git grep -i flag
ast.py:            with open('./flag') as f:
```

```python
class Print(Comm):
    def __init__(self, expr):
        self.expr = expr

    def a_interp(self, env):
        a_val = self.expr.a_interp(env)
        if a_val.infimum < 0:
            raise ValueError("print domain error")
        return env

    def interp(self, env):
        value = self.expr.interp(env)

        if value < 0:
            with open('./flag') as f:
                print(f.read())
        print(value)
        return env
```

Ok, it seems that we just need to print negative integer. Easy!

```
> x=-1;!x
Error: print domain error
```

Nope! Interpreter has two "modes" of execution for each expression: normal
`interp()`, which uses known integer values in obvious way, and `a_interp()`
(abstract interpret?), which uses intervals for everything. For example,
integer literal `42` maps to interval `[42, 42]`, random number `1 ~ 10` maps
to interval `[1, 10]`, expression `(1 ~ 10) + (4)` results in interval
`[5, 14]`.

For any input, challenge service first calls `a_interp()` and only
then `interp()`. So we need to somehow trick `a_interp()` flow to result in
positive interval (so it will not throw an exception) and `interp()` flow to
result in negative value in the same time.

### Solution

After reading [domain.py](./challenge/domain.py), I thought that maybe I could
get NaNs using infinity values, and this will lead me somewhere. But no, this is
not possible because of the following line in constructor:

```python
assert infimum <= supremum
```

`NaN` on either side of the expressions leads to `False`, and thus to
exception.

Then I started to read [ast.py](./challenge/ast.py) (the actual interpreter)
carefully to find possible bugs. And eventually found following implementation
of "while" loop:

```python
class While(Comm):
    ...

    def a_interp(self, env):
        init_env = deepcopy(env)

        for i in range(3):
            tenv, _ = self.cond.a_interp(env)
            if tenv is not None:
                tenv = self.comm.a_interp(tenv)
            env = env_join(env, tenv)

        tenv, _ = self.cond.a_interp(env)
        if tenv is not None:
            tenv = self.comm.a_interp(tenv)
        env = env_widen(env, tenv)

        tenv, _ = self.cond.a_interp(env)
        if tenv is not None:
            tenv = self.comm.a_interp(tenv)
        env = env_join(init_env, tenv)
        _, fenv = self.cond.a_interp(env)

        if fenv is None:
            raise RuntimeError("loop analysis error")

        return fenv

    ...
```

`for i in range(3):` looks very suspicious here. Like it uses only few
iterations of loop to calculate intervals for resulting variables.

After some experimenting, I found the right combination of "while" loop and
if/else:

```
x = 0;
i = 20;
[i > 0 {
    i = i - (1);
    i > 15? {
        x = x + (1)
    } : {
        x = x - (1)
    }
}];
x = x + (1);
!x
```

This code results in value `-11` but positive interval `[0, inf]` for variable
`x`.

Sending it (without the whitespace characters) to the challenge server gave
me the flag:

```
$ nc 58.229.253.56 7777
> x=0;i=20;[i>0{i=i-(1);i>15?{x=x+(1)}:{x=x-(1)}}];x=x+(1);!x
CODEGATE2020{4bstr4ct_1nt3rpr3tat10n_f0r_54f3_3v41uat10n}
```

Source code containing my local experiments is [here](./solution.py).
