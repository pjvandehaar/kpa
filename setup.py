#!/usr/bin/env python3
# to install locally: `pip install -e .`
# to install latest from pypi: `pip3 install --upgrade --upgrade-strategy eager --no-cache-dir kpa`
# to publish: `./setup.py publish`
# to update deps: `kpa pip-find-updates`
# to test: `./setup.py test`

from setuptools import setup
import imp
import sys
from pathlib import Path
from urllib.request import urlopen
import subprocess
import json

version = imp.load_source('kpa.version', 'kpa/version.py').version


if sys.argv[-1] in ['publish', 'pub']:
    # TODO: use `class UploadCommand(setuptools.Command)` from <https://github.com/kennethreitz/setup.py/blob/master/setup.py#L49>

    git_workdir_returncode = subprocess.run('git diff-files --quiet'.split()).returncode
    assert git_workdir_returncode in [0,1]
    if git_workdir_returncode == 1:
        print('git workdir has changes')
        print('please either revert or stage them')
        sys.exit(1)

    pypi_url = 'https://pypi.python.org/pypi/kpa/json'
    latest_version = json.loads(urlopen(pypi_url).read())['info']['version']
    # Note: it takes pypi a minute to update the API, so this can be wrong.
    if latest_version == version:
        new_version_parts = version.split('.')
        new_version_parts[2] = str(1+int(new_version_parts[2]))
        new_version = '.'.join(new_version_parts)
        print(f'autoincrementing version {version} -> {new_version}')
        Path('kpa/version.py').write_text(f"version = '{new_version}'\n")
        version = new_version
        subprocess.run(['git','stage','kpa/version.py'])

    git_index_returncode = subprocess.run('git diff-index --quiet --cached HEAD'.split()).returncode
    assert git_index_returncode in [0,1]
    if git_index_returncode == 1:
        print('git index has changes')
        subprocess.run(['git','commit','-m',version])

    if not Path('~/.pypirc').expanduser().exists():
        print('warning: you need a ~/.pypirc')

    if Path('dist').exists() and list(Path('dist').iterdir()):
        setuppy = Path('dist').absolute().parent / 'setup.py'
        assert setuppy.is_file() and 'kpa' in setuppy.read_text()
        for child in Path('dist').absolute().iterdir():
            assert child.name.startswith('Kpa-'), child
            print('unlinking', child)
            child.unlink()

    subprocess.run('python3 setup.py sdist bdist_wheel'.split(), check=True)
    subprocess.run('twine upload dist/*'.split(), check=True)

    if git_index_returncode == 1:
        print('Now do `git push`.')
    sys.exit(0)


setup(
    name='Kpa',
    version=version,
    description="<forthcoming>",
    author="Peter VandeHaar",
    author_email="pjvandehaar@gmail.com",
    url="https://github.com/pjvandehaar/kpa",
    classifiers=[
        'Programming Language :: Python :: 3 :: Only',
        'Operating System :: Unix',
    ],

    packages=['kpa'],
    entry_points={'console_scripts': [
        'kpa=kpa.command_line:main',
    ]},
    include_package_data=True,
    zip_safe=False,
    python_requires=">=3.6",
    setup_requires=[
        'pytest-runner~=4.2',
    ],
    install_requires=[],
    tests_require=[
        'pytest~=4.0',
    ],
)
