#!/usr/bin/env python3

from pathlib import Path
import pathlib, sys, argparse, os
from typing import Optional


def main() -> None:
    command = sys.argv[1] if sys.argv[1:] else ''

    if command in ['lint', 'l']:
        from .dev_utils import lint_cli
        exit(lint_cli(sys.argv[2:]))

    elif command in ['lw', 'lint-watch', 'wl', 'watch-lint']:
        from .dev_utils import lint_cli
        lint_cli(sys.argv[2:] + ['--watch'])

    elif command in ['watch', 'w']:
        from .watcher import run as watcher_run
        watcher_run(sys.argv[2:])

    elif command in ["pip-find-updates", 'pfu']:
        from .pip_utils import run as pfu_run
        pfu_run(sys.argv[2:])

    elif command == 'skel':
        from .skel import run as skel_run
        skel_run(sys.argv[2:])

    elif command == 'serve-status-code':
        from .http_server import serve, status_code_server
        serve(status_code_server)

    elif command == 'serve-dir':
        from .http_server import serve, magic_directory_server
        serve(magic_directory_server)

    elif command == 'serve-redirect':
        from .http_server import serve, make_redirect_server
        port = int(sys.argv[2])
        target_base_url = sys.argv[3]
        serve(make_redirect_server(target_base_url), port=port)

    elif command in ['term-color', 'termcolor']:
        from .terminal_utils import termcolor
        def r(num): return '#' if num is None else str(num%10)
        print('    # ' + ' '.join('{bg:2}'.format(bg=bg) for bg in range(50)))
        for fg in [None]+list(range(0,25)):
            print('{fg:<2} '.format(fg=(fg if fg is not None else '#')) +
                  ' '.join(termcolor(r(fg)+r(bg), fg, bg) for bg in [None]+list(range(50))))

    else:
        if sys.argv[1:]: print('unknown command:', sys.argv[1:])
        from .version import version
        print(f'kpa version {version}\n')
        print('available commands:\n  kpa termcolor\n  kpa status-code-server\n  kpa redirect-server\n  kpa pip-find-updates')
