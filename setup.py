#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
from setuptools import setup, find_packages

import terracommon

def read(fname):
    return open(fname).read()

setup(
    name = "terra-common",
    version = terracommon.__version__,
    author = terracommon.__author__,
    author_email = terracommon.__email__,
    description = ("The Terra API"),
    url = "https://gitlab.makina-corpus.net/Terralego/Core/terra-back/",

    packages=find_packages(
        exclude=['terracommon.project',
                 'terracommon.project.*',
                 '*.tests']
                 ),

    long_description=read('README.md'),
    classifiers=[
        "Programming Language :: Python",
        "Topic :: Software Development"
    ],
    install_requires=['psycopg2>=2.7,<2.8',
                      'Django>=2.0,<2.1.0',
                      'djangorestframework>=3.7,<3.8',
                      'djangorestframework-gis==0.12',
                      'djangorestframework-jwt>=1.11,<1.12',
                      'drf-yasg>=1.5,<1.6',
    ],
)
