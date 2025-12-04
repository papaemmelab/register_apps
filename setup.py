"""register_apps setup.py."""

from os.path import join
from os.path import abspath
from os.path import dirname

from setuptools import find_packages
from setuptools import setup

ROOT = abspath(dirname(__file__))

# see 4 > https://packaging.python.org/guides/single-sourcing-package-version/
with open(join(ROOT, "register_apps", "VERSION"), "r") as f:
    VERSION = f.read().strip()

setup(
    version=VERSION,
    include_package_data=True,
    packages=find_packages(),
    classifiers=[
        "Intended Audience :: Developers",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: MIT License",
        "Natural Language :: English",
        "Operating System :: Unix",
        "Operating System :: POSIX",
        "Programming Language :: Python :: 3",
        "Topic :: Utilities",
    ],
    entry_points={
        "console_scripts": [
            "register_docker=register_apps.cli:register_docker",
            "register_python=register_apps.cli:register_python",
            "register_singularity=register_apps.cli:register_singularity",
            "register_toil=register_apps.cli:register_toil",
            "register_apps=register_apps.cli:cli",
        ]
    },
    setup_requires=[],
    install_requires=[
        "click>=7.0.0",
        "pyyaml>=6.0",
        "virtualenvwrapper>=4.8.4",
    ],
    extras_require={
        "test": [
            "coverage>=7.0.0",
            "pydocstyle>=6.0.0",
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0",
            "pytest-env>=1.0.0",
            "pylint>=3.0.0",
            "setuptools<80",
            "tox>=4.0.0",
        ]
    },
    author="Juan S. Medina, Juan E. Arango Ossa",
    keywords=[],
    license="BSD",
    name="register_apps",
    test_suite="tests",
    long_description="📘 learn more on `GitHub <https://github.com/papaemmelab/register_apps>`_!",
    description=(
        "👾 Register versioned toil container pipelines and other "
        "commands in singularity containers and python packages."
    ),
    url="https://github.com/papaemmelab/register_apps",
)
