from django.contrib.auth import get_user_model
from django.contrib.auth.forms import SetPasswordForm
from django.contrib.auth.tokens import default_token_generator
from django.contrib.auth.views import PasswordResetConfirmView
from rest_framework import serializers
from rest_framework.serializers import ValidationError

UserModel = get_user_model()


class PasswordChangeSerializer(serializers.Serializer):
    old_password = serializers.CharField(max_length=128, required=False)
    new_password1 = serializers.CharField(max_length=128)
    new_password2 = serializers.CharField(max_length=128)

    set_password_form_class = SetPasswordForm

    def __init__(self, user, **kwargs):
        self.user = user
        super().__init__(**kwargs)

    def validate_old_password(self, value):
        if (self.user.has_usable_password()
                and not self.user.check_password(value)):
            raise ValidationError('Invalid password')
        return value

    def validate(self, attrs):
        if not self.user:
            raise ValidationError({'User': ['Invalid user']})

        self.set_password_form = self.set_password_form_class(
            user=self.user, data=attrs
        )

        if not self.set_password_form.is_valid():
            raise ValidationError(self.set_password_form.errors)
        return attrs

    def save(self):
        return self.set_password_form.save()


class PasswordResetSerializer(PasswordChangeSerializer):
    check_token = default_token_generator.check_token
    get_user = PasswordResetConfirmView.get_user

    def __init__(self, uidb64, token, **kwargs):
        self.uidb64, self.token = uidb64, token
        self.user = self.get_user(self.uidb64)
        super().__init__(self.user, **kwargs)

    def validate(self, attrs):
        if not self.check_token(self.user, self.token):
            raise ValidationError({'token': ['Invalid value']})

        return super().validate(attrs)


class UserProfileSerializer(serializers.ModelSerializer):

    class Meta:
        model = UserModel
        fields = ('uuid', 'email', 'properties')
        read_only_fields = ('uuid', UserModel.USERNAME_FIELD, )


class TerraUserSerializer(serializers.ModelSerializer):
    permissions = serializers.SerializerMethodField()
    groups = serializers.SerializerMethodField()

    def get_groups(self, obj):
        return [group.name for group in obj.groups.all()]

    def get_permissions(self, obj):
        return list(obj.get_all_permissions())

    class Meta:
        model = UserModel
        fields = ('id', 'is_superuser', 'email', 'uuid', 'properties',
                  'is_staff', 'is_active', 'permissions', 'groups')
