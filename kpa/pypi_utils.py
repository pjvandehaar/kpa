from pathlib import Path
import subprocess, sys, shutil, re, urllib.request, json, importlib.util, types
try:
    import tomllib
except ImportError:
    try:
        import tomli as tomllib
    except ImportError:
        raise Exception('=> Please run `pip install tomli` and then try again.')


def upload_package(package_name:str|None, current_version:str='') -> None:
    pyproject_path = Path('pyproject.toml')
    if not package_name and pyproject_path.exists():
        package_name = tomllib.load(pyproject_path.open('rb'))['project']['name']
    if not package_name:
        raise Exception('=> Please specify a package name as argument or in pyproject.toml')
    package_name = package_name.lower()

    ## 1. Find version, either in pyproject.toml or version.py
    version_is_in_pyproject = False
    if pyproject_path.exists():
        try:
            current_version = tomllib.load(pyproject_path.open('rb'))['project']['version']
            version_is_in_pyproject = True
        except Exception:
            pass # Malformed toml or other issue, ignore
    if not current_version:
        # Fallback to version.py
        version_path = Path(f'{package_name}/version.py')
        if not version_path.exists():
            raise Exception(f'Could not find version in pyproject.toml or {package_name}/version.py')        
        current_version = load_module_from_path(version_path).version
    assert current_version, current_version
    
    ## 2. Error if git has workdir changes
    git_workdir_returncode = print_and_run('git diff-files --quiet'.split()).returncode
    assert git_workdir_returncode in [0,1]
    if git_workdir_returncode == 1:
        print('=> Git workdir has changes')
        print('=> Please either revert or stage them')
        sys.exit(1)

    ## 3. Increment version if already used on PyPI
    pypi_url = f'https://pypi.org/pypi/{package_name}/json'
    try:
        latest_version = json.loads(urllib.request.urlopen(pypi_url).read())['info']['version']
    except Exception:
        print(f'=> Could not check PyPI version for {package_name}')
        choice = input('=> Do you want to increment the version? (y/n/abort) ').strip().lower()
        if choice == 'y': latest_version = current_version  # This will trigger the version increment
        elif choice == 'n': latest_version = '' # New package, or failed request
        elif choice == 'abort': sys.exit(1)
        else: raise Exception('=> Invalid choice')

    if latest_version == current_version:
        new_version = next_version(current_version)
        print(f'=> Autoincrementing version {current_version} -> {new_version}')
        if version_is_in_pyproject:
            # Update pyproject.toml, using simple string replace
            content = pyproject_path.read_text()
            pattern = r'(^version\s*=\s*)(["\'])' + re.escape(current_version) + r'\2'
            content, count = re.subn(pattern, f'version = "{new_version}"', content, count=1, flags=re.MULTILINE)
            if not count:
                raise Exception(f'=> Could not find version line matching `version="{current_version}"` in {pyproject_path}')
            pyproject_path.write_text(content)
            print_and_run(['git','stage',str(pyproject_path)], check=True)
            current_version = new_version
        else:
            # Update version.py
            version_path.write_text(f"version = '{new_version}'\n")
            print_and_run(['git','stage',str(version_path)], check=True)
            current_version = new_version

    ## 4. Commit staged changes, if any
    git_index_returncode = print_and_run('git diff-index --quiet --cached HEAD'.split()).returncode
    if git_index_returncode == 1:
        print('=> Git index has changes; committing them')
        print_and_run(['git','commit','-m',current_version], check=True)

    ## 5. Build, publish, and tell user to push if needed
    build()
    publish()
    if git_index_returncode == 1:
        print('=> Now do `git push`.')


def build() -> None:
    ## Clean dist/ , which might not be necessary.
    if Path('dist').exists():
        shutil.rmtree('dist')

    if shutil.which('uv'):
        print_and_run(['uv', 'build'], check=True)
        return

    if importlib.util.find_spec('build'):
        print_and_run([sys.executable, '-m', 'build'], check=True)
        return

    if shutil.which('flit'):
        print_and_run(['flit', 'build', '--no-use-vcs'], check=True)
        return

    raise Exception('=> Please run `pip install build` and then try again.')


def publish() -> None:
    pypirc_path = Path('~/.pypirc').expanduser()
    if not pypirc_path.exists():
        raise Exception('=> Please create ~/.pypirc with your PyPI credentials.')

    if shutil.which('uv'):
        token = re.search(r'password = (\S+)', pypirc_path.read_text()).group(1)
        print_and_run(['uv', 'publish', '--token', token], check=True)
        return

    if shutil.which('twine'):
        print_and_run(['twine', 'upload', '--skip-existing', 'dist/*'], check=True)
        return

    if shutil.which('flit'):
        ## This actually does the build too, which is a waste.
        print_and_run(['flit', 'publish', '--no-use-vcs'], check=True)
        return


def next_version(version:str) -> str:
    version_parts = version.split('.')
    version_parts[-1] = str(1+int(version_parts[-1]))
    return '.'.join(version_parts)
assert next_version('1.1.9') == '1.1.10'
assert next_version('0.0') == '0.1'

def load_module_from_path(filepath:str|Path, module_name:str='') -> types.ModuleType:
    if not module_name: module_name = Path(filepath).name.removesuffix('.py')
    spec = importlib.util.spec_from_file_location(module_name, str(filepath)); assert spec and spec.loader, filepath
    module = importlib.util.module_from_spec(spec); assert module, filepath
    spec.loader.exec_module(module)
    return module

def print_and_run(cmd:list[str], **kwargs):
    print('$$ ' + ' '.join(str(c) for c in cmd))
    return subprocess.run(cmd, **kwargs)
