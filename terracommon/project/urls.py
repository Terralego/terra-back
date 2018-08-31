# -*- coding: utf-8 -*-
from django.conf import settings
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path('api/', include('terracommon.terra.urls')),
    path('api/', include('terracommon.trrequests.urls')),
    path('api/', include('terracommon.accounts.urls')),
    path('api/', include('terracommon.notifications.urls')),
    path('api/', include('terracommon.document_generator.urls')),
]

if settings.DEBUG and 'debug_toolbar' in settings.INSTALLED_APPS:
    import debug_toolbar

    urlpatterns += [
        path('admin/', admin.site.urls),
        path('__debug__/', include(debug_toolbar.urls)),
    ]
