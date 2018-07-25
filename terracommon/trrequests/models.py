from django.conf import settings
from django.contrib.postgres.fields import JSONField
from django.db import models
from django.utils.translation import gettext_lazy as _

from terracommon.terra.models import Feature, Layer

from .helpers import rename_comment_attachment


class BaseUpdatableModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class UserRequest(BaseUpdatableModel):
    owner = models.ForeignKey(settings.AUTH_USER_MODEL,
                              on_delete=models.PROTECT,
                              related_name='userrequests')
    layer = models.ForeignKey(Layer,
                              on_delete=models.PROTECT,
                              related_name='userrequests')
    expiry = models.DateField(default=None, null=True)
    state = models.IntegerField(default=settings.STATES.DRAFT)
    reviewers = models.ManyToManyField(settings.AUTH_USER_MODEL,
                                       blank=True,
                                       related_name='to_review')
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
    attachment = models.FileField(upload_to=rename_comment_attachment,
                                  blank=True)
    filename = models.CharField(max_length=255,
                                editable=False,
                                blank=True,
                                help_text=_('Initial name of the attachment'))

    def save(self, *args, **kwargs):
        if not self.attachment.name.startswith('userrequests/'):
            # Save the name of the new file before upload_to move & rename it
            self.filename = self.attachment.name
        super().save(*args, **kwargs)
