from rest_framework import permissions


class IsOwnerOrStaff(permissions.BasePermission):
    def has_object_permission(self, request, view, object):
        if request.user.is_staff or request.user.is_superuser:
            return True

        return object.owner == request.user


class CanDownloadPdf(IsOwnerOrStaff):
    def has_object_permission(self, request, view, object):
        is_owner_or_staff = super().has_object_permission(
                                                request,
                                                view,
                                                object)

        if not is_owner_or_staff:
            return request.user.has_perm('trrequests.can_download_pdf')

        return is_owner_or_staff
