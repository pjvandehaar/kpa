
from kpa.func_utils import assign
import re, json, urllib.request
from pathlib import Path
from typing import List,Optional


def run(args:List[str]) -> None:
    @assign
    def filepath() -> Optional[str]:
        if args:
            p = Path(args[0])
            if not p.exists(): print("args[0] doesn't exist!"); exit(1)
            return p.as_posix()
        p = Path().absolute()
        for directory in [p] + list(p.parents):
            for filename in ['setup.py', 'requirements.txt']:
                p = directory / filename
                if p.exists(): return p.as_posix()
        return None
    if not filepath: print("No setup.py or requirements.txt here or in parent dirs")
    else:
        print(f'Looking at {filepath}')
        check_file(filepath)


def check_file(filepath:str) -> None:
    with open(filepath) as f:
        for line in f:
            m = re.match(r'''^\s*'?([-a-zA-Z]+)(\[[a-zA-Z]+\])?([~<>=]{2}[0-9a-zA-Z\.]+)?'?,?\s*$''', line)
            if m:
                pkg, opt, version = m.group(1), m.group(2), m.group(3)
                check_pkg(pkg, opt, version, line)

def check_pkg(pkg:str, opt:str, version:str, line:Optional[str] = None) -> None:
    '''
    pkg is like "requests"
    opt is like "[security]" or ""
    version is like ">=4.0"
    line is for debugging
    '''
    if opt is None: opt=''
    if version is None: version=''
    try:
        j = json.loads(urllib.request.urlopen('https://pypi.org/pypi/{}/json'.format(pkg)).read())
        latest = j['info']['version']
        v = version.lstrip('~=>')
        update_str = '' if latest == v or latest==v+'.0' or latest.startswith(v) else '>>'
        print('{:<2} {:20} {:10} {:10}'.format(update_str, pkg+opt, version, latest))
    except Exception:
        raise Exception([pkg, opt, version, line])
