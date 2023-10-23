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
    print_and_run python3 -m pip install flake8
    echo -e "#!/bin/bash\n./tests/lint.sh" > .git/hooks/pre-commit
    print_and_run chmod a+x .git/hooks/pre-commit
    echo "=> Installed pre-commit hook!"
    exit 0
fi

if ! exists flake8 && [[ -e ~/pv/venv/bin/ ]]; then
    PATH=$PATH:$HOME/pv/venv/bin/
fi

if ! exists flake8; then
    echo "Missing flake8 ; Please run: pip3 install flake8"
else
    flake8 --show-source --extend-exclude=".#*" --ignore=E501,E302,E251,E701,E226,E305,E225,E261,E231,E301,E306,E402,E704,E265,E201,E202,E303,E124,E241,E127,E266,E221,E126,E129,F811,E222,E401,E702,E203,E116,E228,W504,B007,E271,F401,E128,W291,W293,E252,E741,E115,E122,E713 *.py kpa/*.py
    echo "finished flake8"
fi

if ! exists mypy; then
    echo "Missing mypy ; Please run: pip3 install mypy && mypy --install-types ."
else
    # Consider using `--check-untyped-defs`
    mypy --pretty --ignore-missing-imports --non-interactive --install-types *.py kpa/*.py
fi

echo FINISHED
