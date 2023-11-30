# Alternatives:
##  - watchfiles.watch(): needs `pip3 install watchfiles`, which installs [anyio, idna, sniffio].  Seems fine.
##  - watchexec: needs `cargo` to install

import time, os, sys, subprocess as subp
from typing import List,Dict,Iterator,Any

try: import watchfiles
except ImportError: have_watchfiles = False
else: have_watchfiles = True


def run(args:List[str]) -> None:
    if not args:
        print('Usage:')
        print('  kpa watch ./serve.py --port=8000   # Re-runs when serve.py changes')
        print('  kpa watch utils.py -- kpa lint utils.py  # Re-runs when utils.py changes')
        sys.exit(1)
    elif '--' in args:
        dashdash_index = args.index('--')
        filepaths = args[:dashdash_index]
        cmd = args[dashdash_index+1:]
    else:
        filepaths = [args[0]]
        cmd = args
        if os.path.exists(filepaths[0]) and not filepaths[0].startswith(('/','./')):
            cmd[0] = './'+cmd[0]

    print(f'Watching {repr(filepaths)} and running {cmd}\n')
    for changeset in yield_when_files_update(filepaths, and_also_immediately=True):
        if changeset is not None: print()
        print('======>', cmd)
        subp.run(cmd)
        print('.')



def yield_when_files_update(filepaths:List[str], and_also_immediately:bool = False) -> Iterator[Any]:
    assert isinstance(filepaths, list)
    if and_also_immediately: yield None
    if have_watchfiles:
        for changeset in watchfiles.watch(*filepaths, raise_interrupt=False):
            yield changeset or {}
    else:
        mtimes = get_mtimes(filepaths)
        while True:
            time.sleep(0.5)
            new_mtimes = get_mtimes(filepaths)
            if new_mtimes != mtimes:
                updated_paths = [p for p in filepaths if mtimes[p]!=new_mtimes[p]]
                #print("Files were updated:", updated_paths)
                yield updated_paths
            mtimes = new_mtimes

def get_mtimes(filepaths:List[str]) -> Dict[str,float]: return {p:get_mtime(p) for p in filepaths}
def get_mtime(filepath:str) -> float: return os.stat(filepath).st_mtime
