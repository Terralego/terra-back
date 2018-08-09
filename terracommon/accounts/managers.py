from django.contrib.auth.base_user import BaseUserManager
from django.contrib.contenttypes.models import ContentType
from django.db.models import Manager, ObjectDoesNotExist


class TerraUserManager(BaseUserManager):

    def _create_user(self, email, password, **extra_fields):
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, password, **extra_fields):
        extra_fields.setdefault('is_staff', False)
        extra_fields.setdefault('is_superuser', False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        return self._create_user(email, password, **extra_fields)


class ReadModelManager(Manager):
    def get_object_content_type(self, obj):
        return ContentType.objects.get_for_model(obj.__class__)

    def get_user_read(self, user, obj):
        contenttype = self.get_object_content_type(obj)
        try:
            return self.get(
                user=user,
                contenttype=contenttype,
                identifier=obj.pk)
        except ObjectDoesNotExist:
            return None

    def read_object(self, user, obj):
        contenttype = self.get_object_content_type(obj)
        read, is_new = self.get_or_create(
                        user=user,
                        contenttype=contenttype,
                        identifier=obj.pk)

        if not is_new:
            read.read_instance()

        return read
