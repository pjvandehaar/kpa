
from kpa.func_utils import assign
import re, json, urllib.request, functools
import subprocess as subp
from pathlib import Path
from typing import List,Optional,Dict


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
    print('{:<2} {:20} {:11} {:11} {:11}'.format('', 'PACKAGE', 'SPEC', 'LATEST', 'INSTALLED'))
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
        latest_version = j['info']['version']
        v = version.lstrip('~=>')
        installed_version = get_installed_pkg_versions2().get(pkg.lower(),'-')
        update_str = (' ' if latest_version.startswith(v) else '>') + (' ' if installed_version.startswith(v) else '>')
        print('{:<2} {:20} {:11} {:11} {:11}'.format(update_str, pkg+opt, version, latest_version, installed_version))
    except Exception:
        raise Exception([pkg, opt, version, line])

@functools.cache
def get_installed_pkg_versions() -> Dict[str,str]:
    try: lines = subp.check_output(['pip3','freeze'], stderr=subp.DEVNULL).decode().split('\n')
    except subp.CalledProcessError: return {}
    ret = {}
    for line in lines:
        if '==' in line:
            pkg, version = line.split('==', 1)
            ret[pkg.lower()] = version
    return ret

@functools.cache
def get_installed_pkg_versions2() -> Dict[str,str]:
    try: lines = subp.check_output(['pip3','list'], stderr=subp.DEVNULL).decode().split('\n')
    except subp.CalledProcessError: return {}
    ret = {}
    for idx, line in enumerate(lines):
        if idx==0 and 'Package' in line or '-----' in line or not line.strip(): continue
        parts  = line.split()
        if len(parts) in (2,3):
            pkg, version = parts[:2]
            ret[pkg.lower()] = version if len(parts)==2 else f'{version}(editable)'
    return ret
