from django.db import models
from django.contrib.auth.models import User
from django.contrib.postgres.fields import JSONField

from terra.models import Feature


class BaseUpdatableModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class Organization(models.Model):
    owner = models.ManyToManyField(User, related_name='organizations')
    properties = JSONField(default=dict, blank=True)


class Request(BaseUpdatableModel):
    owner = models.ForeignKey(User,
                              on_delete=models.PROTECT,
                              related_name='requests')
    feature = models.ForeignKey(Feature,
                                on_delete=models.PROTECT,
                                related_name='requests')
    organization = models.ForeignKey(Organization,
                                     on_delete=models.PROTECT,
                                     related_name='requests')
    properties = JSONField(default=dict, blank=True)


class Comment(BaseUpdatableModel):
    owner = models.ForeignKey(User,
                              on_delete=models.PROTECT)
    request = models.ForeignKey(Request,
                                on_delete=models.PROTECT,
                                related_name="comments")
    feature = models.ForeignKey(Feature,
                                null=True,
                                on_delete=models.PROTECT)
    properties = JSONField(default=dict, blank=True)
