from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.contrib.postgres.fields import JSONField
from django.db import models
from django.db.models.manager import BaseManager

from .managers import DataStoreQuerySet


class DataStore(models.Model):
    key = models.CharField(max_length=255, primary_key=True, )
    value = JSONField(default=dict, blank=False)

    objects = BaseManager.from_queryset(DataStoreQuerySet)()


class DataStorePermission(models.Model):
    group = models.ForeignKey(Group, on_delete=models.CASCADE)
    prefix = models.CharField(max_length=255, blank=False, null=False)
    permission = models.ForeignKey(Permission, on_delete=models.CASCADE)

    class Meta:
        permissions = (
            ('can_read_datastore', "Is able to read all datastore's elements"),
            ('can_readwrite_datastore', 'Is able to write in datastore'),
        )

def related_document_path(instance, filename):
    return (f'documents/{instance.contenttype}/'
            f'{instance.identifier}/{instance.key}')


class RelatedDocument(models.Model):
    key = models.CharField(max_length=255, blank=False)
    model_object = GenericForeignKey('contenttype', 'identifier')
    contenttype = models.ForeignKey(ContentType, on_delete=models.PROTECT)
    identifier = models.PositiveIntegerField()
    document = models.FileField(upload_to=related_document_path, null=False)

    class Meta:
        unique_together = ('key', 'contenttype', 'identifier')
