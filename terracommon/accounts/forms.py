from django.contrib.auth import get_user_model
from django.contrib.auth.forms import PasswordResetForm

UserModel = get_user_model()


class PasswordSetAndResetForm(PasswordResetForm):
    def get_users(self, email):
        """We override django get_users method since we need also users with
           unusable password"""
        active_users = UserModel._default_manager.filter(**{
            '%s__iexact' % UserModel.get_email_field_name(): email,
        })
        return (u for u in active_users)
