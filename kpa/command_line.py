#!/usr/bin/env python3

def main():
    import sys

    if sys.argv[1:] == ['status-code-server']:
        from .http_server import serve
        serve()

    else:
        print('unknown command:', sys.argv[1:])
