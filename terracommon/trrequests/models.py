from django.conf import settings
from django.contrib.postgres.fields import JSONField
from django.db import models

from terracommon.terra.models import Feature, Layer


class BaseUpdatableModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class Organization(models.Model):
    owner = models.ManyToManyField(settings.AUTH_USER_MODEL,
                                   related_name='organizations')
    properties = JSONField(default=dict, blank=True)


class UserRequest(BaseUpdatableModel):
    owner = models.ForeignKey(settings.AUTH_USER_MODEL,
                              on_delete=models.PROTECT,
                              related_name='userrequests')
    layer = models.ForeignKey(Layer,
                              on_delete=models.PROTECT,
                              related_name='userrequests')
    organization = models.ManyToManyField(Organization,
                                          related_name='userrequests')
    state = models.IntegerField()
    properties = JSONField(default=dict, blank=True)

    class Meta:
        permissions = (
            ('can_administrate', 'Has administrator permissions on requests'),
            ('can_read_self', 'Is able to get own requests'),
            ('can_read_all', 'Is able to get all requests'),
            ('can_comment', 'Is able to comment an user request'),
            ('can_internal_comment', 'Is able to add comments not visible by users'),
            ('can_change_state', 'Is authorized to change the request state'),
            ('can_approve', 'Is able to set the approved state'),
        )


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
