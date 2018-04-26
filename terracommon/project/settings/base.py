"""
Django settings

For more information on this file, see
https://docs.djangoproject.com/en/2.0/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/2.0/ref/settings/
"""
import os

CUSTOM_APPS = (
    'core',
    'terra',
    'trrequests',
)

for app in CUSTOM_APPS:
    try:
        app_module = __import__(app, globals(), locals(), ["settings"])
        app_settings = getattr(app_module, "settings", None)

        for setting in dir(app_settings):
            if setting == setting.upper():
                globals()[setting] = getattr(app_settings, setting)

    except ImportError as e:
        pass

INSTALLED_APPS += CUSTOM_APPS
