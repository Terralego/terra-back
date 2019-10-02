# -*- coding: utf-8 -*-
import tempfile

from django.utils import six

from .base import *  # noqa

AUTH_USER_MODEL = 'accounts.TerraUser'

REST_FRAMEWORK['TEST_REQUEST_DEFAULT_FORMAT'] = 'json'
REST_FRAMEWORK['DEFAULT_PERMISSION_CLASSES'] = [
    'rest_framework.permissions.IsAuthenticatedOrReadOnly'
]

SECRET_KEY = 'spam-spam-spam-spam'

MEDIA_ROOT = tempfile.gettempdir()

EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# Boost perf a little
PASSWORD_HASHERS = (
    'django.contrib.auth.hashers.MD5PasswordHasher',
)

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.dummy.DummyCache',
    }
}

# Force every loggers to use null handler only. Note that using 'root'
# logger is not enough if children don't propage.
for logger in six.itervalues(LOGGING['loggers']):  # noqa
    logger['handlers'] = ['console']


DEFAULT_FILE_STORAGE = 'django.core.files.storage.FileSystemStorage'
MEDIA_URL = 'http://testserver/'

try:
    from .local import *  # noqa
except ImportError:
    pass
