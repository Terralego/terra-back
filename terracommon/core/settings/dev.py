# -*- coding: utf-8 -*-
import logging
import os
from datetime import timedelta

from django.utils import six

from . import *

SECRET_KEY = 'dev-dev-dev-dev-dev-dev-dev'

ALLOWED_HOSTS = []
DEBUG = True

EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

INSTALLED_APPS += (  # noqa
    'django_extensions',
)

INTERNAL_IPS = ('127.0.0.1',)  # Used by app debug_toolbar

# Add the Python core NullHandler to be available when needed
LOGGING['handlers']['null'] = {  # noqa
    'level': logging.NOTSET,
    'class': 'logging.NullHandler',
}

DATABASES = {
    'default': {
        'ENGINE': 'django.contrib.gis.db.backends.postgis',
        'NAME': os.environ.get('POSTGRES_DB'),
        'USER': os.environ.get('POSTGRES_USER'),
        'PASSWORD': os.environ.get('POSTGRES_PASSWORD'),
        'HOST': 'db',
        'PORT': '',
    }
}

# Force every loggers to use console handler only. Note that using 'root'
# logger is not enough if children don't propage.
for logger in six.itervalues(LOGGING['loggers']):  # noqa
    logger['handlers'] = ['console']
# Log every level.
LOGGING['handlers']['console']['level'] = logging.NOTSET  # noqa

CORS_ORIGIN_ALLOW_ALL = True

JWT_AUTH['JWT_EXPIRATION_DELTA'] = timedelta(hours=12)
