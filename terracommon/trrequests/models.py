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
    state = models.IntegerField(default=settings.STATES.DRAFT)
    properties = JSONField(default=dict, blank=True)

    class Meta:
        permissions = (
            ('can_create_requests', 'Is able to create a new requests'),
            ('can_read_self_requests', 'Is able to get own requests'),
            ('can_read_all_requests', 'Is able to get all requests'),
            ('can_comment_requests', 'Is able to comment an user request'),
            ('can_internal_comment_requests',
             'Is able to add comments not visible by users'),
            ('can_change_state_requests',
             'Is authorized to change the request state'),
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
    is_internal = models.BooleanField(default=False)
