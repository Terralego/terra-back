#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup, find_packages

import terracommon


def read(fname):
    return open(fname).read()


setup(
    name="terra-common",
    version=terracommon.__version__,
    author=terracommon.__author__,
    author_email=terracommon.__email__,
    description="The Terra API",
    url="https://gitlab.makina-corpus.net/Terralego/Core/terra-back/",
    packages=find_packages(
        exclude=["terracommon.project", "terracommon.project.*", "*.tests"]
    ),
    include_package_data=True,
    long_description=read("README.md"),
    classifiers=[
        "Programming Language :: Python",
        "Topic :: Software Development",
        "License :: OSI Approved :: GNU Affero General Public License v3",
    ],
    install_requires=[
        "psycopg2>=2.7,<2.8",
        "Django>=2.0,<2.1.0",
        "djangorestframework>=3.7,<3.8",
        "djangorestframework-gis==0.12",
        "djangorestframework-jwt>=1.11,<1.12",
        "drf-yasg>=1.9,<2.0",
        "django-cors-headers>=2.2,<2.3",
        "simpleeval>=0.9,<1.0",
        "requests>=2.19,<2.20",
        "mercantile>=1.0,<1.1",
        "django-url-filter>=0.3,<0.4",
        "Fiona>=1.7,<1.8",
        "python-magic>=0.4,<0.5",
        "docxtpl>=0.5,<0.6",
        "Pillow>=5.3.0,<6.0.0",
        "django-storages>=1.7,<1.8",
        "django-versatileimagefield>=1.10,<2.0",
        "boto3>=1.9,<=1.10",
        "deepmerge<=1.0",
    ],
)
