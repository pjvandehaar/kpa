
def run(filepath:str = ''):
    run_flake8(filepath)
    run_mypy(filepath)

def run_flake8(filepath:str = ''):
    import subprocess, sys
    p = subprocess.run(['flake8', '--show-source', '--ignore=E501,E302,E251,E701,E226,E305,E225,E261,E231,E301,E306,E402,E704,E265,E201,E202,E303,E124,E241,E127,E266,E221,E126,E129,F811,E222,E401,E702,E203,E116,E228,W504,W293,B007,W391,F401', filepath])
    if p.returncode != 0: sys.exit(1)

def run_mypy(filepath:str = ''):
    import subprocess, sys
    p = subprocess.run(['mypy', '--pretty', '--ignore-missing-imports'] + ([filepath] if filepath else []))
    if p.returncode != 0: sys.exit(1)
