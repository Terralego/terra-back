from django.contrib.postgres.fields import JSONField
from django.db import models


class EventHandler(models.Model):
    action = models.CharField(max_length=255, blank=False, null=False)
    handler = models.CharField(max_length=255, blank=False, null=False)
    settings = JSONField(default=dict)
    priority = models.PositiveIntegerField(default=10)

    class Meta:
        ordering = ['id']
