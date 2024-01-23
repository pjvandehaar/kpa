#!/usr/bin/env python3

import sys
from pathlib import Path
from typing import List


def run(argv:List[str]) -> None:
    command = argv[0] if argv else ''
    if command == 'tests/lint.sh': create_lint_sh()
    elif command.endswith('.sh'): create_bash(command)
    else:
        print(f"Unknown command: {repr(command)}")
        print('Usage:')
        print('  kpa skel tests/lint.sh')
        print('  kpa skel $script.sh')


lint_sh_text = '''\
#!/bin/bash
## This script does simple static-checking of this codebase.
## Run `./tests/lint.sh install` to make this run every time you run `git commit`.
set -euo pipefail
readlinkf() { perl -MCwd -le 'print Cwd::abs_path shift' "$1"; }
SCRIPTDIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
exists() { type -t "$1" >/dev/null; }
print_and_run() { echo "=> $@" >&2; "$@"; echo >&2; }
cd "$SCRIPTDIR/.."

if [[ ${1:-} == install ]]; then
    print_and_run python3 -m pip install flake8 mypy kpa
    echo -e "#!/bin/bash\n./tests/lint.sh" > .git/hooks/pre-commit
    print_and_run chmod a+x .git/hooks/pre-commit
    echo "=> Installed pre-commit hook!"
    exit 0
fi

if [[ ${1:-} == watch ]]; then
    kpa lint --watch
else
    kpa lint
fi

echo FINISHED
'''

def create_lint_sh() -> None:
    lint_sh_path = Path('tests/lint.sh')
    lint_sh_path.parent.mkdir(exist_ok=True)
    if not lint_sh_path.exists(): lint_sh_path.write_text(lint_sh_text)

bash_text = '''\
#!/bin/bash
set -euo pipefail
readlinkf() { perl -MCwd -le 'print Cwd::abs_path shift' "$1"; }
SCRIPTDIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
exists() { type -t "$1" >/dev/null; }
print_and_run() { echo "=> $@"; "$@"; echo; }
cd "$SCRIPTDIR"

'''

def create_bash(filepath:str) -> None:
    p = Path(filepath)
    p.parent.mkdir(exist_ok=True)
    if p.exists() and '-f' not in sys.argv: print(f"Cannot create {filepath} because it already exists!  Consider using `-f`."); exit(1)
    p.write_text(bash_text)
