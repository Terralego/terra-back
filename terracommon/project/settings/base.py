"""
Django settings

For more information on this file, see
https://docs.djangoproject.com/en/2.0/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/2.0/ref/settings/
"""
import os
from importlib import import_module

CUSTOM_APPS = (
    'terracommon.core',
    'terracommon.terra',
    'terracommon.trrequests',
    'terracommon.accounts',
    'terracommon.notifications',
    'terracommon.data_importers',
    'terracommon.events',
    'terracommon.document_generator',
    'terracommon.datastore',
    'terracommon.tropp',
)

# Import app specific settings
for app in CUSTOM_APPS:
    try:
        app_settings = import_module(f"{app}.settings", ["settings"])

        for setting in dir(app_settings):
            if setting == setting.upper():
                globals()[setting] = getattr(app_settings, setting)

    except ImportError as e:
        pass

DEFAULT_FILE_STORAGE = 'django.core.files.storage.FileSystemStorage'

INSTALLED_APPS += CUSTOM_APPS
