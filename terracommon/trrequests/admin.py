from django.contrib import admin

from .models import Organization, UserRequest


admin.site.register(Organization)
admin.site.register(UserRequest)
