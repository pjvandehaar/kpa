#!/usr/bin/env python3
# to install: `pip install -e .`
# to upgrade: `pip3 install --upgrade --upgrade-strategy eager --no-cache-dir kpa`
# to publish: `python3 setup.py publish`
# to test: `python3 setup.py test`


from setuptools import setup
import imp
import sys

version = imp.load_source('kpa.version', 'kpa/version.py').version

if sys.argv[-1] == 'publish':
    from pathlib import Path
    import subprocess, urllib.request, json
    resp = urllib.request.urlopen('https://pypi.python.org/pypi/kpa/json')
    latest_version = json.loads(resp.read())['info']['version']
    # Note: it takes pypi a minute to update the API, so this can be wrong.
    if latest_version == version:
        new_version_parts = version.split('.')
        new_version_parts[2] = str(1+int(new_version_parts[2]))
        new_version = '.'.join(new_version_parts)
        print(f'autoincrementing version {version} -> {new_version}')
        Path('kpa/version.py').write_text(f"version = '{new_version}'\n")
    if not Path('~/.pypirc').expanduser().exists():
        print('warning: you need ~/.pypirc')
    if Path('dist').exists() and list(Path('dist').iterdir()):
        print('warning: cleaning out dist/*')
        setuppy = Path('dist').absolute().parent / 'setup.py'
        assert setuppy.is_file() and 'kpa' in setuppy.read_text()
        for child in Path('dist').absolute().iterdir():
            assert child.name.startswith('kpa-')
            print('unlinking', child)
            child.unlink()
    subprocess.check_output('python3 setup.py sdist bdist_wheel'.split())
    subprocess.check_output('twine upload dist/*'.split())
    sys.exit(0)

setup(
    name='kpa',
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
        'pytest-runner~=4.0',
    ],
    install_requires=[],
    tests_require=[
        'pytest~=3.4',
    ],
)
