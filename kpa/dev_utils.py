import time, random, sys, argparse, os, subprocess as subp
from pathlib import Path
from functools import wraps
from typing import Optional,Iterator,List

class ExecutableNotFound(Exception): pass

def lint(filepath:str = '', make_cache:bool = True, run_rarely:bool = False) -> None:
    if run_rarely:
        seconds_since_last_change = time.time() - Path(filepath).stat().st_mtime
        if seconds_since_last_change > 30 and random.random() > 0.01:
            return  # Don't run
    lint_flake8(filepath)
    lint_mypy(filepath, make_cache=make_cache)
run = lint

def lint_flake8(filepath:str = '') -> None:
    try: flake8_exe = find_exe('flake8', filepath=filepath)
    except ExecutableNotFound: return None
    p = subp.run([flake8_exe, '--show-source', '--ignore=E501,E302,E251,E701,E226,E305,E225,E261,E231,E301,E306,E402,E704,E265,E201,E202,E303,E124,E241,E127,E266,E221,E126,E129,F811,E222,E401,E702,E203,E116,E228,W504,W293,B007,W391,F401,W292,E227,E128', filepath])
    if p.returncode != 0: sys.exit(1)

def lint_mypy(filepath:str = '', make_cache:bool = True) -> None:
    try: mypy_exe = find_exe('mypy', filepath=filepath)
    except ExecutableNotFound: return None
    cmd = [mypy_exe, '--pretty', '--ignore-missing-imports']
    if not make_cache: cmd.append('--cache-dir=/dev/null')
    if filepath: cmd.append(filepath)
    p = subp.run(cmd)
    if p.returncode != 0: sys.exit(1)

def find_exe(name:str, filepath:str = '') -> str:
    for path in find_exe_options(name, filepath=filepath):
        if os.path.exists(path): return path
    print(f"[Failed to find {name}]")
    raise ExecutableNotFound()
def find_exe_options(name:str, filepath:str = '') -> Iterator[str]:
    try: yield subp.check_output(['which',name]).decode().strip()
    except Exception: pass
    yield f'venv/bin/{name}'
    if filepath: yield f'{os.path.dirname(os.path.abspath(filepath))}/venv/bin/{name}'


def lint_cli(argv:List[str]) -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('files', nargs='+')
    #parser.add_argument('--no-mypy-cache', action='store_true', help="Don't make .mypy_cache/")
    parser.add_argument('--run-rarely', action='store_true', help="Only when file is modified in last 30 seconds, or otherwise 1% of the time")
    parser.add_argument('--extra-flake8-ignores', help="Extra errors/warnings for flake8 to ignore")
    parser.add_argument('--venv-bin-dir', help="A path to venv/bin that has flake8 or mypy")
    parser.add_argument('--verbose', action='store_true')
    args = parser.parse_args(argv)

    if args.run_rarely:
        seconds_since_last_change = time.time() - max(Path(path).stat().st_mtime for path in args.files)
        if seconds_since_last_change > 30 and random.random() > 0.01: exit(0)

    def find_exe(name:str) -> str:
        for path in find_exe_options(name):
            if os.path.exists(path): return path
        print(f"[Failed to find {name}]")
        raise ExecutableNotFound()
    def find_exe_options(name:str) -> Iterator[str]:
        if args.venv_bin_dir: yield f'{args.venv_bin_dir}/{name}'
        try: yield subp.check_output(['which',name]).decode().strip()
        except Exception: pass
        yield f'venv/bin/{name}'
        for file in args.files: yield f'{os.path.dirname(os.path.abspath(file))}/venv/bin/{name}'
    def print_and_run(cmd:List[str]) -> None:
        if args.verbose: print(cmd)
        p = subp.run(cmd)
        if p.returncode != 0: print(f"\n{cmd[0]} failed"); exit(1)

    flake8_ignore = 'B007,E116,E124,E126,E127,E128,E129,E201,E202,E203,E221,E222,E225,E226,E227,E228,E231,E241,E251,E261,E265,E266,E301,E302,E303,E305,E306,E401,E402,E501,E701,E702,E704,F401,F811,W292,W293,W391,W504'
    if args.extra_flake8_ignores: flake8_ignore += ',' + args.extra_flake8_ignores
    try: flake8_exe = find_exe('flake8')
    except ExecutableNotFound: pass
    else: print_and_run([flake8_exe, '--show-source', f'--ignore={flake8_ignore}', *args.files])

    try: mypy_exe = find_exe('mypy')
    except ExecutableNotFound: pass
    else: print_and_run([mypy_exe, '--pretty', '--ignore-missing-imports', '--non-interactive', '--install-types', *args.files])


def get_size(obj, seen:Optional[set] = None) -> int:
    """Recursively calculates bytes of RAM taken by object"""
    # From https://code.activestate.com/recipes/577504/ and https://github.com/bosswissam/pysize/blob/master/pysize.py
    if seen is None: seen = set()
    size = sys.getsizeof(obj)
    obj_id = id(obj)
    if obj_id in seen:
        return 0
    seen.add(obj_id)  # Mark as seen *before* recursing to handle self-referential objects

    if isinstance(obj, dict):
        size += sum(get_size(v, seen) for v in obj.values())
        size += sum(get_size(k, seen) for k in obj.keys())
    elif hasattr(obj, '__dict__'):
        size += get_size(obj.__dict__, seen)
    elif hasattr(obj, '__iter__') and not isinstance(obj, (str, bytes, bytearray)):
        size += sum(get_size(i, seen) for i in obj)

    if hasattr(obj, '__slots__'):  # obj can have both __slots__ and __dict__
        size += sum(get_size(getattr(obj, s), seen) for s in obj.__slots__ if hasattr(obj, s))

    return size
