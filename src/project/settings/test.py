# -*- coding: utf-8 -*-
import tempfile

from django.utils import six

from .base import *  # noqa


SECRET_KEY = 'spam-spam-spam-spam'

MEDIA_ROOT = tempfile.gettempdir()

EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# Boost perf a little
PASSWORD_HASHERS = (
    'django.contrib.auth.hashers.MD5PasswordHasher',
)

# Force every loggers to use null handler only. Note that using 'root'
# logger is not enough if children don't propage.
for logger in six.itervalues(LOGGING['loggers']):  # noqa
    logger['handlers'] = ['console']


try:
    from .local import *  # noqa
except ImportError:
    pass
