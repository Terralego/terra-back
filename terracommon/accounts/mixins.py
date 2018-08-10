from .models import ReadModel


class ReadableModelMixin(object):
    def user_read(self, user):
        if not user:
            raise AttributeError('Cannot set element read for unknown user')
        ReadModel.objects.read_object(user, self)

    def get_user_read(self, user):
        return ReadModel.objects.get_user_read(user, self)
