import uuid

from django.contrib.auth import get_user_model
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models

UserModel = get_user_model()


class DocumentTemplate(models.Model):
    name = models.CharField(max_length=50)
    documenttemplate = models.FileField(upload_to='templates/%Y/%m/')
    uid = models.CharField(max_length=256, default=uuid.uuid4)

    class Meta:
        ordering = ['id']
        permissions = (
            ('can_upload_template', 'Is allowed to upload a template'),
            ('can_update_template', 'Is allowed to update a template'),
            ('can_delete_template', 'Is allowed to delete a template'),
        )


class DownloadableDocument(models.Model):
    user = models.ForeignKey(UserModel, on_delete=models.PROTECT)
    document = models.ForeignKey(DocumentTemplate, on_delete=models.PROTECT)

    content_type = models.ForeignKey(ContentType, on_delete=models.PROTECT)
    object_id = models.PositiveIntegerField()
    linked_object = GenericForeignKey('content_type', 'object_id')

    class Meta:
        ordering = ['id']
