from django.conf import settings
from django.contrib.postgres.fields import JSONField
from django.db import models

from terracommon.terra.models import Feature


class BaseUpdatableModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class Organization(models.Model):
    owner = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='organizations')
    properties = JSONField(default=dict, blank=True)


class UserRequest(BaseUpdatableModel):
    owner = models.ForeignKey(settings.AUTH_USER_MODEL,
                              on_delete=models.PROTECT,
                              related_name='userrequests')
    feature = models.ForeignKey(Feature,
                                on_delete=models.PROTECT,
                                related_name='userrequests')
    organization = models.ManyToManyField(Organization, related_name='userrequests')
    properties = JSONField(default=dict, blank=True)


class Comment(BaseUpdatableModel):
    owner = models.ForeignKey(settings.AUTH_USER_MODEL,
                              on_delete=models.PROTECT)
    userrequest = models.ForeignKey(UserRequest,
                                    on_delete=models.PROTECT,
                                    related_name="comments")
    feature = models.ForeignKey(Feature,
                                null=True,
                                on_delete=models.PROTECT)
    properties = JSONField(default=dict, blank=True)
