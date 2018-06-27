from django.contrib.auth import get_user_model
from django.contrib.auth.forms import SetPasswordForm
from django.contrib.auth.tokens import default_token_generator
from django.contrib.auth.views import PasswordResetConfirmView
from rest_framework import serializers
from rest_framework.serializers import ValidationError

UserModel = get_user_model()


class PasswordResetSerializer(serializers.Serializer):
    old_password = serializers.CharField(max_length=128, required=False)
    new_password1 = serializers.CharField(max_length=128)
    new_password2 = serializers.CharField(max_length=128)

    check_token = default_token_generator.check_token
    get_user = PasswordResetConfirmView.get_user
    set_password_form_class = SetPasswordForm

    def __init__(self, uidb64, token, **kwargs):
        self.uidb64, self.token = uidb64, token
        self.user = self.get_user(self.uidb64)
        super().__init__(**kwargs)

    def validate_old_password(self, value):
        """If the user is active, old_password is needed"""
        if (self.user.has_usable_password()
                and not self.user.check_password(value)):
                raise ValidationError('Invalid password')
        return value

    def validate(self, attrs):
        if not self.check_token(self.user, self.token):
            raise ValidationError({'token': ['Invalid value']})

        if not self.user:
            raise ValidationError({'uidb64': ['Invalid value']})

        self.set_password_form = self.set_password_form_class(
            user=self.user, data=attrs
        )

        if not self.set_password_form.is_valid():
            raise ValidationError(self.set_password_form.errors)

        return attrs

    def save(self):
        return self.set_password_form.save()


class UserProfileSerializer(serializers.ModelSerializer):

    class Meta:
        model = UserModel
        fields = ('uuid', 'email', 'properties')
        read_only_fields = ('uuid', UserModel.USERNAME_FIELD, )
