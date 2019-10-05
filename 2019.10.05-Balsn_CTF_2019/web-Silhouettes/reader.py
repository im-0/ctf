#!/usr/bin/env python3

import glob


fname = glob.glob('c:/*~*')
if fname:
    fname = fname[0]
    print('fname: %r' % (fname, ))
    try:
        with open(fname, 'r') as f:
            print('GOT FLAG: ', f.read())
    except:
        print('GOT FLAG (NO): open()')
else:
    print('GOT FLAG (NO): glob.glob()')
