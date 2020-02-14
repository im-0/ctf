#!/usr/bin/python3

from ply import yacc

import challib.parser


def _eval(prog):
    prog = prog.replace(' ', '').replace('\n', '')
    print('! program:')
    print('!    ', prog)

    ast = yacc.parse(prog)
    print('! interp:')
    print('!    ', ast.interp({}))
    print('! a_interp:')
    print('!    ', ast.a_interp({}))
    print()


def _main():
    _eval('''
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
    ''')

    return

    # Simple.
    _eval('''
        a = 123;
        !a
    ''')

    # Loop.
    _eval('''
        x = 0;
        i = 5;
        d = -1;
        [i > 0 {
            i = i + d;
            x = x + d;
            !i
        }]
    ''')

    # Random.
    _eval('''
        i = 10;
        d = -1;
        [i > 0 {
            i = i + d;
            x = 1 ~ 4;
            !x
        }]
    ''')

    # If/else.
    _eval('''
        x = 0;
        i = 5;
        d = -1;
        [i > 0 {
            i = i + d;
            i == 0? {
                x = 0
            } : {
                x = 123
            };
            !i
        }];
        !x
    ''')

    #  Playground.
    _eval('''
        minf = 0;
        i = 20;
        test = 0;
        [i > 0 {
            i = i - (1);
            minf = minf - (1);
            i > 14? {
                test = test + (1)
            } : {
                test = test - (1)
            }
        }];
        test = test + (1);

        pinf = 0;
        i = 1;
        [i > 0 {
            i = i - (1);
            pinf = pinf + (1)
        }];

        minfpinf = minf + pinf
    ''')


_main()
