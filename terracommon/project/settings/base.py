"""
Django settings

For more information on this file, see
https://docs.djangoproject.com/en/2.0/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/2.0/ref/settings/
"""
import copy
import os
from datetime import timedelta
from importlib import import_module

from django.utils.log import DEFAULT_LOGGING
from terra_utils.helpers import Choices

PROJECT_DIR = os.path.abspath('.')
PUBLIC_DIR = os.path.join(PROJECT_DIR, 'public')
PROJECT_NAME = os.environ.get('PROJECT_PACKAGE')
DEFAULT_FILE_STORAGE = 'django.core.files.storage.FileSystemStorage'

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/2.0/howto/deployment/checklist/

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False

ALLOWED_HOSTS = []

MIDDLEWARE = (
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'django.middleware.security.SecurityMiddleware',
)

ROOT_URLCONF = PROJECT_NAME + '.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(PROJECT_DIR, 'templates')],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'django.template.context_processors.i18n',
            ],
        },
    },
]

REST_FRAMEWORK = {
    'TEST_REQUEST_DEFAULT_FORMAT': 'json',
    'DEFAULT_PAGINATION_CLASS':
        'terra_utils.pagination.PagePagination',
    'PAGE_SIZE': 100,
    'DEFAULT_PARSER_CLASSES': (
        'rest_framework.parsers.JSONParser',
        'rest_framework.parsers.FormParser',
        'rest_framework.parsers.MultiPartParser'
    ),
    'DEFAULT_RENDERER_CLASSES': (
        'rest_framework.renderers.JSONRenderer',
        'rest_framework.renderers.BrowsableAPIRenderer',
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
    ),
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_jwt.authentication.JSONWebTokenAuthentication',
        'rest_framework.authentication.SessionAuthentication',
        'rest_framework.authentication.BasicAuthentication',
    ),
}


# JWT configuration
# http://getblimp.github.io/django-rest-framework-jwt/
JWT_AUTH = {
    'JWT_ENCODE_HANDLER': 'rest_framework_jwt.utils.jwt_encode_handler',
    'JWT_DECODE_HANDLER': 'rest_framework_jwt.utils.jwt_decode_handler',
    'JWT_PAYLOAD_HANDLER': 'terra_accounts.jwt_payload.terra_payload_handler',
    'JWT_PAYLOAD_GET_USER_ID_HANDLER': 'rest_framework_jwt.utils.jwt_get_user_id_from_payload_handler',
    'JWT_RESPONSE_PAYLOAD_HANDLER': 'rest_framework_jwt.utils.jwt_response_payload_handler',
    # 'JWT_SECRET_KEY': settings.SECRET_KEY,
    'JWT_GET_USER_SECRET_KEY': None,
    'JWT_PUBLIC_KEY': None,
    'JWT_PRIVATE_KEY': None,
    'JWT_ALGORITHM': 'HS256',
    'JWT_VERIFY': True,
    'JWT_VERIFY_EXPIRATION': True,
    'JWT_LEEWAY': 0,
    'JWT_EXPIRATION_DELTA': timedelta(seconds=300),
    'JWT_AUDIENCE': None,
    'JWT_ISSUER': None,
    'JWT_ALLOW_REFRESH': True,
    'JWT_REFRESH_EXPIRATION_DELTA': timedelta(days=7),
    'JWT_AUTH_HEADER_PREFIX': 'JWT',
    'JWT_AUTH_COOKIE': None,
}

WSGI_APPLICATION = PROJECT_NAME + '.wsgi.application'

# Internationalization
# https://docs.djangoproject.com/en/2.0/topics/i18n/
LOCALE_PATHS = (
    os.path.join(PROJECT_DIR, 'locales'),
)
LANGUAGE_CODE = 'fr-fr'
TIME_ZONE = 'Europe/Paris'
USE_I18N = True
USE_L10N = True
USE_TZ = True

DATABASES = {
    'default': {
        'ENGINE': 'django.contrib.gis.db.backends.postgis',
        'NAME': os.environ.get('POSTGRES_DB'),
        'USER': os.environ.get('POSTGRES_USER'),
        'PASSWORD': os.environ.get('POSTGRES_PASSWORD'),
        'HOST': os.environ.get('POSTGRES_HOST', 'db'),
        'PORT': '',
    }
}

FORMAT_MODULE_PATH = [
    PROJECT_NAME + '.formats',
]

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/2.0/howto/static-files/

STATIC_URL = '/static/'
STATICFILES_DIRS = ()
STATIC_ROOT = os.path.join(PUBLIC_DIR, 'static')

MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(PUBLIC_DIR, 'media')

# Just to be easily override by children conf files.
LOGGING = copy.deepcopy(DEFAULT_LOGGING)

AUTH_USER_MODEL = 'terra_accounts.TerraUser'

REQUEST_SCHEMA = {}

# Geometrical projection used internaly in database
# Note: Other projection than 4326 are not yet supported by some part of code
INTERNAL_GEOMETRY_SRID = 4326

MAX_TILE_ZOOM = 15 # Vector tiles are usable on display up to max zoom + 3
MIN_TILE_ZOOM = 10

TERRA_APPLIANCE_SETTINGS = {}
FRONT_URL = os.environ.get('FRONT_URL', '')
HOSTNAME = os.environ.get('HOSTNAME', '')

TERRA_TILES_HOSTNAMES = [
    HOSTNAME,
]

MEDIA_ACCEL_REDIRECT = False

CUSTOM_APPS = (
    'terracommon.trrequests',
    'terracommon.notifications',
    'terracommon.data_importers',
    'terracommon.events',
    'terracommon.document_generator',
    'terracommon.datastore',
)

INSTALLED_APPS = (
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.gis',
    'rest_framework',
    'rest_framework_gis',
    'versatileimagefield',
    'drf_yasg',
    'corsheaders',
    'geostore',
    'terra_utils',
    'terra_accounts',
)
INSTALLED_APPS += CUSTOM_APPS

# Import app specific settings
for app in CUSTOM_APPS:
    try:
        app_settings = import_module(f"{app}.settings", ["settings"])

        for setting in dir(app_settings):
            if setting == setting.upper():
                globals()[setting] = getattr(app_settings, setting)

    except ImportError as e:
        pass
