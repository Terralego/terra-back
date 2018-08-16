from django.contrib.auth.tokens import default_token_generator
from django.contrib.auth.views import PasswordResetConfirmView
from rest_framework.permissions import BasePermission


class TokenBasedPermission(BasePermission):
    get_user = PasswordResetConfirmView.get_user

    def has_permission(self, request, view):
        assert 'uidb64' in request.GET and 'token' in request.GET

        user = self.get_user(request.GET['uidb64'])
        print(user)
        print(request.GET['token'])
        if default_token_generator.check_token(user, request.GET['token']):
            view.request.user = user
            return True

        return False
