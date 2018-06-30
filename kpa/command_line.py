#!/usr/bin/env python3

def main():
    import sys

    if sys.argv[1:] == ['status-code-server']:
        from .http_server import serve, status_code_app
        serve(status_code_app)

    elif sys.argv[1:] == ['termcolor']:
        from .terminal_utils import termcolor
        def r(num): return '#' if num is None else str(num%10)
        print('    # ' + ' '.join(f'{bg:2}' for bg in range(50)))
        for fg in [None]+list(range(0,25)):
            print(f'{fg if fg is not None else "#":<2} ' +
                  ' '.join(termcolor(r(fg)+r(bg), fg, bg) for bg in [None]+list(range(50))))

    else:
        # TODO: print all options
        print('unknown command:', sys.argv[1:])
