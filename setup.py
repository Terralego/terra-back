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
        "django-geostore==0.3.1",  # old terracommon.terra
        "python-magic>=0.4",
        "djangorestframework-jwt>=1.11,<1.12",
        "django-cors-headers>=2.2,<2.3",
        "django-url-filter>=0.3,<0.4",
        "django-storages>=1.7,<1.8",
        "django-versatileimagefield>=1.10,<2.0",
        "boto3>=1.9,<=1.10",
        "weasyprint>=44",
        "simpleeval>=0.9",
        "docxtpl>=0.5",
    ],
)
