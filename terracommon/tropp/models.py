from django.conf import settings
from django.contrib.gis.db import models
from django.contrib.postgres.fields import JSONField
from django.utils.translation import ugettext_lazy as _
from versatileimagefield.fields import VersatileImageField

from terracommon.core.mixins import BaseUpdatableModel
from terracommon.terra.models import Feature


class BaseLabelModel(BaseUpdatableModel):
    label = models.CharField(_('Label'), max_length=100)

    class Meta:
        abstract = True

    def __str__(self):
        return self.label


class Theme(BaseLabelModel):
    pass


class Viewpoint(BaseLabelModel):
    point = models.ForeignKey(
        Feature,
        on_delete=models.CASCADE,
        related_name='points',
    )
    themes = models.ManyToManyField(
        Theme,
        related_name='viewpoints',
        blank=True
    )
    properties = JSONField(_('Properties'), default=dict, blank=True)

    class Meta:
        permissions = (
            ('can_download_pdf', 'Is able to download a pdf document'),
        )


class Campaign(BaseLabelModel):
    viewpoints = models.ManyToManyField(
        Viewpoint,
        related_name='campaigns',
    )
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        verbose_name=_('Owner'),
        related_name='campaigns',
    )
    assignee = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        verbose_name=_('Assigned to'),
        related_name='assigned_campaigns',
    )


class Picture(BaseUpdatableModel):
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        verbose_name=_('Owner'),
        related_name='pictures',
    )
    viewpoint = models.ForeignKey(
        Viewpoint,
        on_delete=models.PROTECT,
        related_name='pictures',
    )
    # States may be : draft, metadata_ok (submitted), accepted, refused
    state = models.IntegerField(_('State'), default=settings.STATES.DRAFT)

    properties = JSONField(_('Properties'), default=dict, blank=True)
    file = VersatileImageField(_('File'))

    # Different from created_at which is the upload date
    date = models.DateTimeField(_('Date'))

    # TODO maybe move that to another model with GenericFK?
    remarks = models.TextField(_('Remarks'), max_length=350)

    class Meta:
        permissions = (
            ('can_change_state_picture', 'Is able to change the picture '
                                         'state'),
        )
        # It's our main way of sorting pictures, so it better be indexed
        indexes = [
            models.Index(fields=['viewpoint', 'date']),
        ]
        get_latest_by = 'date'


class Document(BaseUpdatableModel):
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        verbose_name=_('Owner'),
        related_name='documents',
    )
    viewpoint = models.ForeignKey(
        Viewpoint,
        on_delete=models.PROTECT,
        related_name='documents',
    )
    properties = JSONField(_('Properties'), default=dict, blank=True)
    file = models.FileField(_('File'))
