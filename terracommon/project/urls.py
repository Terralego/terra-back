# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from django.conf import settings
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path('api/', include('terracommon.terra.urls')),
    path('admin/', admin.site.urls),
]

if settings.DEBUG and 'debug_toolbar' in settings.INSTALLED_APPS:
    import debug_toolbar

    urlpatterns += [
        path('__debug__/', include(debug_toolbar.urls)),
    ]
