from django.conf import settings
from django.contrib.contenttypes.fields import GenericRelation
from django.contrib.postgres.fields import JSONField
from django.db import models
from django.db.models import Q
from django.utils.translation import gettext_lazy as _
from geostore.models import Layer

from terracommon.accounts.mixins import ReadableModelMixin
from terracommon.core.mixins import BaseUpdatableModel
from terracommon.datastore.models import RelatedDocument
from terracommon.document_generator.models import DownloadableDocument

from .helpers import rename_comment_attachment


class UserRequest(BaseUpdatableModel, ReadableModelMixin):
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
    downloadable = GenericRelation(DownloadableDocument)
    documents = GenericRelation(RelatedDocument)

    def get_comments_for_user(self, user):
        query = self.comments.all()
        if not user:
            return query.none()

        filter = Q()

        # exclude comments if the user have no permission
        if not user.has_perm(
                'trrequests.can_internal_comment_requests'):
            filter |= Q(is_internal=True)

        if (not user.has_perm('trrequests.can_comment_requests') and
                not user.has_perm('trrequests.can_read_comment_requests')):
            filter |= Q(is_internal=False)

        return query.exclude(filter)

    def get_serializer(self):
        # Exceptionnally,
        # to avoid circular dependencies between model and serializer
        from .serializers import UserRequestSerializer

        return UserRequestSerializer

    def get_pdf_serializer(self):
        # Avoid circular dependencies
        from .serializers import UserRequestPDFSerializer
        return UserRequestPDFSerializer

    class Meta:
        ordering = ['id']
        permissions = (
            ('can_create_requests', 'Is able to create a new requests'),
            ('can_read_self_requests', 'Is able to get own requests'),
            ('can_read_all_requests', 'Is able to get all requests'),
            ('can_comment_requests', 'Is able to comment an user request'),
            ('can_internal_comment_requests',
             'Is able to add comments not visible by users'),
            ('can_read_comment_requests',
             'Is allowed to read only non-internal comments'),
            ('can_change_state_requests',
             'Is authorized to change the request state'),
            ('can_download_all_pdf',
             'Is able to download a pdf document')
        )


class Comment(BaseUpdatableModel):
    owner = models.ForeignKey(settings.AUTH_USER_MODEL,
                              on_delete=models.PROTECT)
    userrequest = models.ForeignKey(UserRequest,
                                    on_delete=models.PROTECT,
                                    related_name="comments")
    layer = models.ForeignKey(Layer,
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

    class Meta:
        ordering = ['id']
