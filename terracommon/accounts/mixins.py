from django.contrib.auth.tokens import default_token_generator
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode

from .models import ReadModel


class ReadableModelMixin(object):

    def user_read(self, user):
        if not user:
            raise AttributeError('Cannot set element read for unknown user')
        ReadModel.objects.read_object(user, self)

    def get_user_read(self, user):
        return ReadModel.objects.get_user_read(user, self)


class UserTokenGeneratorMixin(object):
    def get_uidb64_token_for_user(self, user):
        return (urlsafe_base64_encode(force_bytes(user.pk)).decode(),
                default_token_generator.make_token(self.current_user))
