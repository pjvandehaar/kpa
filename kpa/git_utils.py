#!/usr/bin/env python3

import sys, os, re, subprocess as subp, contextlib, datetime, argparse
from pathlib import Path
from typing import Iterator, Sequence
from kpa.terminal_utils import termcolor


def run(argv:list[str]) -> None:
    # parser = argparse.ArgumentParser()
    # parser.add_argument('pos_args', nargs='*', help='summary | status | urls | list | run-on-each')
    # parser.add_argument('--recurse-levels', '-r', type=int, default=0, help='how many levels down to search for .git')
    # args = parser.parse_args(argv)
    # arg = args.pos_args[0] if args.pos_args else ''
    # repos = find_git_repos('', recurse_levels=args.recurse_levels)

    recurse_levels = 0
    pos_args = []
    for arg in argv:
        if re.fullmatch(r'-([0-9])', arg):
            recurse_levels = int(arg[1:])
        else:
            pos_args.append(arg)

    parent_dir = ''
    if pos_args and Path(pos_args[0]).is_dir():
        parent_dir = pos_args[0]
        arg = pos_args[1] if pos_args[1:] else ''
    else:
        arg = pos_args[0] if pos_args else ''
    repos = find_git_repos(parent_dir, recurse_levels=recurse_levels)

    if arg in ['','summary']:
        for repo in repos:
            with set_cwd(repo):
                remotes = check_output(['git','-C',repo,'remote']).split()
                ## 1. Show url + branch (if not master/main)
                url = check_output(['git','remote','get-url','origin']) if remotes else '(no remote)'
                git_dir = Path(check_output(['git','rev-parse','--absolute-git-dir']))
                git_head = (git_dir / 'HEAD').read_text().replace('ref:','').replace('refs/heads/','').strip()
                if git_head in ['master','main']:
                    print(f'=> {repo.name:16} {url}')
                else:
                    print(f'=> {repo.name:16} {url}    [{git_head}]')
                ## 2. Show modified files
                changes = check_output(['git','status','--short'])
                if changes:
                    print(termcolor(indent(changes), bg=termcolor.BG_RED))  # TODO: head -5
                ## 3. Show whether ahead/behind origin.
                if remotes:
                    remote = remotes[0]
                    remote_branch = git_head  # TODO: `git config --get branch.{branch}.merge`.replace('refs/heads/','')
                    remote_ref = f'refs/remotes/{remote}/{remote_branch}'
                    num_unpushed_commits = check_output(['git','rev-list','--no-merges','--count',f'{remote_ref}..HEAD'])
                    if num_unpushed_commits != '0':
                        print(termcolor(f'  {num_unpushed_commits} unpushed commits ({git_head}..{remote_ref})', bg=termcolor.BG_RED))
        if {'--pull','--fetch'}.intersection(sys.argv):
            print('\nNow fetching all... ', end='', flush=True)
            for repo in repos:
                with set_cwd(repo):
                    print(repo.name[0], end='', flush=True)
                    ## TODO: If there's anything to fetch, make sure to print which repo fetched.
                    subp.run(['git','fetch','--quiet'])


    elif arg == 'list':
        for repo in repos: print(repo)

    elif arg in ['status','stat','s','si']:
        for repo in repos:
            cmd = ['git','-C',str(repo),'status','--short']
            if arg=='si': cmd.append('--ignored')
            output = check_output(cmd)
            if not output: continue
            print('=>', repo)
            print(output)
            print()

    elif arg in ['url','urls']:
        for repo in repos:
            remotes = check_output(['git','-C',repo,'remote']).split()
            if not remotes:
                print(f'{repr(str(repo))}  (no remotes)')
            else:
                lines = check_output(['git','-C',repo,'config','--get-regexp',r'remote\..*\.url']).split('\n')
                remote_urls = {line.split()[0].split('.')[1]: line.split()[1] for line in lines}
                out = []
                for remote_name, remote_url in remote_urls.items():
                    if remote_name == 'origin': out.append(remote_url)
                    else: out.append(f'{remote_name}=remote_url')
                print(f'{repr(str(repo))}    {" ".join(out)}')

    elif arg in ['run','run-on-each']:
        command = argv[1:]
        print(command)
        for repo in repos:
            with set_cwd(repo):
                print(f'\n=> {str(repo):25}', command)
                proc = subp.run(command)
                if proc.returncode != 0:
                    print(f'[returncode={proc.returncode}]')

    else: raise Exception(f'Unknown command "{arg}"')


def print_and_run(cmd:Sequence[str|Path], **kwargs) -> None:
    assert isinstance(cmd, list)
    cmd = [str(c) for c in cmd]
    log(cmd)
    subp.run(cmd, check=True, **kwargs)

def log(*args) -> None:
    time_str = datetime.datetime.now().strftime('%H:%M:%S')
    print(f'[{time_str}]', *args, flush=True)

@contextlib.contextmanager
def set_cwd(path:str|Path) -> Iterator[None]:
    old_cwd = os.getcwd()
    os.chdir(path)
    yield
    os.chdir(old_cwd)

def indent(text:str) -> str: return '\n'.join('  '+line for line in text.split('\n'))

def check_output(cmd:Sequence[str|Path], **kwargs) -> str:
    cmd_str = [str(c) for c in cmd]
    return subp.check_output(cmd_str, **kwargs, text=True).strip()

def check_retcode_and_output(cmd:Sequence[str|Path], **kwargs) -> tuple[int,str]:
    cmd = [str(c) for c in cmd]
    proc = subp.run(cmd, **kwargs, text=True, stdout=subp.PIPE, stderr=subp.STDOUT)
    return (proc.returncode, proc.stdout)

def find_git_repos(parent_dir:Path|str|None=None, recurse_levels:int=0) -> Iterator[Path]:
    parent = Path(parent_dir or '').absolute()
    dirs = [d for d in parent.iterdir() if d.is_dir()]
    for d in dirs:
        if (d / '.git/config').is_file():
            yield d
        else:
            if recurse_levels >= 1:
                yield from find_git_repos(d, recurse_levels=recurse_levels-1)



if __name__ == '__main__':
    run(sys.argv[1:])
