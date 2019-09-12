from django.contrib.auth.tokens import default_token_generator
from django.contrib.auth.views import PasswordResetConfirmView
from rest_framework.permissions import (SAFE_METHODS, BasePermission,
                                        IsAuthenticated)


class TokenBasedPermission(BasePermission):
    get_user = PasswordResetConfirmView.get_user

    def has_permission(self, request, view):
        if 'uidb64' in request.GET and 'token' in request.GET:
            user = self.get_user(request.GET['uidb64'])

            if default_token_generator.check_token(user, request.GET['token']):
                view.request.user = user
                return True

        return False


class IsAuthenticatedPost(IsAuthenticated):
    def has_object_permission(self, request, view, *args, **kwargs):
        return self.has_permission(request, view)

    def has_permission(self, request, view):
        if request.method not in SAFE_METHODS:
            return super().has_permission(request, view)
        return False


class IsPostOrToken(TokenBasedPermission, IsAuthenticatedPost):
    def has_permission(self, *args):
        return (TokenBasedPermission.has_permission(self, *args)
                or IsAuthenticatedPost.has_permission(self, *args))


class GroupAdminPermission(BasePermission):
    def has_permission(self, request, view):
        return request.user.has_perm('accounts.can_manage_groups')
