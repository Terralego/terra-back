from django.contrib.auth import get_user_model
from django.db import models

from .managers import NotificationManager

UserModel = get_user_model()

LEVELS = (
    ('DEBUG', 'Debug'),
    ('INFO', 'Information'),
    ('SUCCESS', 'Succès'),
    ('WARNING', 'Avertissement'),
    ('ERROR', 'Erreur')
)


class UserNotifications(models.Model):
    user = models.ForeignKey(UserModel,
                             on_delete=models.PROTECT,
                             related_name='notifications')
    created_at = models.DateTimeField(auto_now_add=True)
    read = models.BooleanField(default=False)
    level = models.CharField(choices=LEVELS, max_length=255, blank=False)
    event_code = models.CharField(max_length=255)
    message = models.TextField(blank=True)
    identifier = models.IntegerField()
    uuid = models.UUIDField(null=True)

    objects = NotificationManager()

    class Meta:
        ordering = ['id']
