from django.contrib.auth.models import Permission
from rest_framework.permissions import SAFE_METHODS, IsAuthenticated

from .models import DataStore


class IsAuthenticatedAndDataStoreAllowed(IsAuthenticated):
    def has_object_permission(self, request, view, obj):
        permissions = ['can_readwrite_datastore', ]

        if request.method in SAFE_METHODS:
            permissions.append('can_read_datastore')

        perms = Permission.objects.filter(codename__in=permissions)

        return DataStore.objects.get_datastores_for_user(
                    request.user, perms).filter(key=obj.key).exists()
