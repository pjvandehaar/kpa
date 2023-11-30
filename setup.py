#!/usr/bin/env python3
# to install locally: `pip install -e .`
# to install latest from pypi: `pip3 install -U --upgrade-strategy=eager --no-cache-dir kpa`
# to publish: `./setup.py publish`

from setuptools import setup
import importlib.util, types, sys


def load_module_by_path(module_name:str, filepath:str) -> types.ModuleType:
    spec = importlib.util.spec_from_file_location(module_name, filepath); assert spec and spec.loader
    module = importlib.util.module_from_spec(spec); assert module
    spec.loader.exec_module(module)
    return module
version = load_module_by_path('kpa.version', 'kpa/version.py').version


if sys.argv[-1] in ['publish', 'pub']:
    pypi_utils = load_module_by_path('kpa.pypi_utils', 'kpa/pypi_utils.py')
    pypi_utils.upload_package(package_name='Kpa')
    sys.exit(0)


setup(
    name='Kpa',
    version=version,
    description="Simple python utils",
    author="Peter VandeHaar",
    author_email="pjvandehaar@gmail.com",
    url="https://github.com/pjvandehaar/kpa",
    classifiers=[
        'Programming Language :: Python :: 3 :: Only',
        'Operating System :: Unix',
    ],

    package_data={'kpa': ['py.typed']},  # tells mypy this has types
    packages=['kpa'],
    entry_points={'console_scripts': [
        'kpa=kpa.command_line:main',
    ]},
    include_package_data=True,
    zip_safe=False,
    python_requires=">=3.6",
    install_requires=[],
)
