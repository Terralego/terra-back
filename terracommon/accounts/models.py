import uuid

from django.contrib.auth import get_user_model
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.contrib.gis.db import models
from django.contrib.postgres.fields import JSONField
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from .managers import ReadModelManager, TerraUserManager


class TerraUser(AbstractBaseUser, PermissionsMixin):
    USERNAME_FIELD = 'email'
    EMAIL_FIELD = 'email'
    REQUIRED_FIELDS = []

    uuid = models.CharField(_('unique identifier'),
                            max_length=255,
                            default=uuid.uuid4,
                            editable=False,
                            unique=True)
    email = models.EmailField(_('email address'), blank=True, unique=True)
    properties = JSONField(default=dict, blank=True)
    is_staff = models.BooleanField(
        _('staff status'),
        default=False,
        help_text=_('Designates whether the user '
                    'can log into this admin site.'),
    )
    is_active = models.BooleanField(
        _('active'),
        default=True,
        help_text=_(
            'Designates whether this user should be treated as active. '
            'Unselect this instead of deleting accounts.'
        ),
    )
    date_joined = models.DateTimeField(_('date joined'), default=timezone.now)

    objects = TerraUserManager()

    class Meta:
        ordering = ['id']
        permissions = (
            ('can_manage_users', 'Is able create, delete, update users'),
        )


UserModel = get_user_model()


class ReadModel(models.Model):
    user = models.ForeignKey(UserModel, on_delete=models.PROTECT)
    contenttype = models.ForeignKey(ContentType, on_delete=models.PROTECT)
    identifier = models.PositiveIntegerField()
    model_object = GenericForeignKey('contenttype', 'identifier')
    last_read = models.DateTimeField(auto_now=True)

    objects = ReadModelManager()

    def read_instance(self):
        self.save()

    class Meta:
        ordering = ['id']
