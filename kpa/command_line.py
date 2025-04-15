#!/usr/bin/env python3

from pathlib import Path
import pathlib, sys, argparse, os
from typing import Optional


help_template = '''\
kpa version {version}

available commands:
  kpa lint
  kpa lint-watch
  kpa watch
  kpa skel
  kpa pip-find-updates
  kpa termcolor
  kpa serve-status-code (status-code-server)
  kpa redirect-server
  kpa llm
'''

def main() -> None:
    command = sys.argv[1] if sys.argv[1:] else ''

    ## TODO: Add lwr which watches, lints, and runs.

    if command in ['lint', 'l']:
        from .dev_utils import lint_cli
        exit(lint_cli(sys.argv[2:]))

    elif command in ['lw', 'lint-watch', 'wl', 'watch-lint']:
        from .dev_utils import lint_cli
        lint_cli(sys.argv[2:] + ['--watch'])

    elif command in ['watch', 'w']:
        from .watcher import run as watcher_run
        watcher_run(sys.argv[2:])

    elif command == 'llm':
        from .llm_utils import run_llm_command
        run_llm_command(sys.argv[2:])

    elif command in ["pip-find-updates", 'pfu']:
        from .pip_utils import run as pfu_run
        pfu_run(sys.argv[2:])

    elif command == 'skel':
        from .skel import run as skel_run
        skel_run(sys.argv[2:])

    elif command in ['serve-status-code', 'status-code-server']:
        from .http_server import serve, status_code_server
        serve(status_code_server)

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
        if sys.argv[1:] and sys.argv[1] not in ['-h','--help']: print('unknown command:', sys.argv[1:], '\n')
        from .version import version
        print(help_template.format(version=version))
