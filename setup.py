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
    long_description_content_type="text/markdown",
    classifiers=[
        "Programming Language :: Python",
        "Topic :: Software Development",
        "License :: OSI Approved :: MIT License",
    ],
    install_requires=[
        "psycopg2>=2.7,<2.8",
        "Django>=2.1,<2.2",
        "djangorestframework>=3.8,<3.9",
        "djangorestframework-gis>=0.14,<0.15",
        "djangorestframework-jwt>=1.11,<1.12",
        "drf-yasg>=1.9,<1.10",
        "django-cors-headers>=2.2,<2.3",
        "simpleeval>=0.9,<1.0",
        "requests>=2.19,<2.20",
        "mercantile>=1.0,<1.1",
        "django-url-filter>=0.3,<0.4",
        "Fiona>=1.8,<1.9",
        "python-magic>=0.4,<0.5",
        "docxtpl>=0.5,<0.6",
        "Pillow>=5.3.0,<6.0.0",
        "django-storages>=1.7,<1.8",
        "django-versatileimagefield>=1.10,<2.0",
        "boto3>=1.9,<=1.10",
        "deepmerge<=1.0",
        "weasyprint>=44",
        "jsonschema>=3.0,<3.1",
        "docutils<0.15",
    ],
)
