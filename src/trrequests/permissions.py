from rest_framework import permissions


class IsOwnerOrStaff(permissions.BasePermission):
    def has_object_permission(self, request, view, object):
        if request.user.is_staff or request.user.is_superuser:
            return True

        return object.owner == request.user
