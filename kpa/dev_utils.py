import time, random, sys
from pathlib import Path
from functools import wraps

def run(filepath:str = '', make_cache:bool = True, run_rarely:bool = False) -> None:
    if run_rarely:
        seconds_since_last_change = time.time() - Path(filepath).stat().st_mtime
        if seconds_since_last_change > 30 and random.random() > 0.01:
            return  # Don't run
    run_flake8(filepath)
    run_mypy(filepath, make_cache=make_cache)

def run_flake8(filepath:str = '') -> None:
    import subprocess, sys
    p = subprocess.run(['flake8', '--show-source', '--ignore=E501,E302,E251,E701,E226,E305,E225,E261,E231,E301,E306,E402,E704,E265,E201,E202,E303,E124,E241,E127,E266,E221,E126,E129,F811,E222,E401,E702,E203,E116,E228,W504,W293,B007,W391,F401,W292,E227,E128', filepath])
    if p.returncode != 0: sys.exit(1)

def run_mypy(filepath:str = '', make_cache:bool = True) -> None:
    import subprocess, sys
    cmd = ['mypy', '--pretty', '--ignore-missing-imports']
    if not make_cache: cmd.append('--cache-dir=/dev/null')
    if filepath: cmd.append(filepath)
    p = subprocess.run(cmd)
    if p.returncode != 0: sys.exit(1)


def get_size(obj, seen:set = None) -> int:
    """Recursively finds size of objects"""
    # Question: Does this function consume iterators?
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
