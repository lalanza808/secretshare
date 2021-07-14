# -*- coding: utf-8 -*-

from setuptools import setup, find_packages
from secretshare import __version__

NAME = "secretshare"
DESCRIPTION = "Flask application for sharing secrets using AWS Secrets Manager"
URL = "https://github.com/lalanza808/secretshare"
EMAIL = "lance@lzatech.org"
AUTHOR = "Lance Allen"
REQUIRES_PYTHON = ">=3.6.0"
VERSION = __version__
REQUIRED = [
    "arrow",
    "boto3",
    "flask-restx",
    "werkzeug",
    "Flask",
    "Flask-Cors",
    "zappa"
]
EXTRAS = {
}
TESTS = [
]
SETUP = [
]

setup(
    name=NAME,
    version=VERSION,
    description=DESCRIPTION,
    author=AUTHOR,
    author_email=EMAIL,
    include_package_data=True,
    extras_require=EXTRAS,
    install_requires=REQUIRED,
    setup_requires=SETUP,
    tests_require=TESTS,
    packages=find_packages(exclude=['ez_setup']),
    zip_safe=False
)
