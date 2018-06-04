#!/usr/bin/env python3
# to install: `pip install -e .`
# to upgrade: `pip3 install --upgrade --upgrade-strategy eager --no-cache-dir kpa`
# to publish: `python3 setup.py publish`
# to test: `python3 setup.py test`


from setuptools import setup
import imp
import sys

if sys.argv[-1] == 'publish':
    import pathlib, subprocess
    # TODO: auto-increment version
    if not pathlib.Path('~/.pypirc').expanduser().exists(): print('warning: you need ~/.pypirc')
    if list(pathlib.Path('dist').iterdir()): print('warning: dist/* may cause problems')
    subprocess.check_output('python3 setup.py sdist bdist_wheel'.split())
    subprocess.check_output('twine upload dist/*'.split())


version = imp.load_source('kpa.version', 'kpa/version.py').version

setup(
    name='kpa',
    version=version,
    description="<forthcoming>",
#    author="Peter VandeHaar",
#    author_email="pjvandehaar@gmail.com",
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
