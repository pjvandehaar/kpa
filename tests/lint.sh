#!/bin/bash
## This script does simple static-checking of this codebase.
## Run `./tests/lint.sh install` to make this run every time you run `git commit`.
set -euo pipefail
readlinkf() { perl -MCwd -le 'print Cwd::abs_path shift' "$1"; }
SCRIPTDIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
exists() { type -t "$1" >/dev/null; }
print_and_run() { echo "=> $@"; "$@"; echo; }
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
