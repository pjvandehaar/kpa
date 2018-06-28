#!/usr/bin/env python3

def main():
    import sys

    if sys.argv[1:] == ['status-code-server']:
        from .http_server import serve
        serve()

    elif sys.argv[1:] == ['termcolor']:
        from .terminal_utils import termcolor
        def r(num): return '#' if num is None else str(num%10)
        for fg in [None]+list(range(0,25)):
            print(' '.join(termcolor(r(fg)+r(bg), fg, bg) for bg in [None]+list(range(50))))


    else:
        # TODO: print all options
        print('unknown command:', sys.argv[1:])
