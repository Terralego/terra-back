from django.conf import settings
from django.contrib.postgres.fields import JSONField
from django.db import models
from django.utils.translation import ugettext_lazy as _

from terracommon.core.mixins import BaseUpdatableModel
from terracommon.terra.models import Layer


class LabelBasedModel(BaseUpdatableModel):
    label = models.CharField(_('Label'), max_length=100)

    class Meta:
        abstract = True

    def __str__(self):
        return self.label


class Theme(LabelBasedModel):
    content = models.TextField(_('Content'))

    class Meta:
        verbose_name = _('Theme')


class ObservationPoint(LabelBasedModel):
    theme = models.ManyToManyField(
        Theme,
        verbose_name=_('Theme'),
        related_name='observation_points',
    )
    layer = models.ForeignKey(
        Layer,
        on_delete=models.PROTECT,
        verbose_name=_('Layer'),
        related_name='observation_points',
    )
    # FIXME GeoJSON field ?
    properties = JSONField(_('Properties'), default=dict, blank=True)
    remarks = models.TextField(_('Remarks'), max_length=350)

    class Meta:
        permissions = (
            ('can_download_pdf', 'Is able to download a pdf document'),
        )
        verbose_name = _('Observation point')
        verbose_name_plural = _('Observation points')


class Campaign(LabelBasedModel):
    observation_points = models.ManyToManyField(
        ObservationPoint,
        verbose_name=_('Observation points'),
        related_name='campaigns',
    )
    # TODO Permission to edit a campaign
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        verbose_name=_('Owner'),
        related_name='campaigns',
    )


class Picture(BaseUpdatableModel):
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        verbose_name=_('Owner'),
        related_name='pictures',
    )
    point = models.ForeignKey(
        ObservationPoint,
        on_delete=models.PROTECT,
        verbose_name=_('Point'),
        related_name='pictures',
    )
    state = models.IntegerField(_('State'), default=settings.STATES.DRAFT)
    properties = JSONField(_('Properties'), default=dict, blank=True)
    file = models.ImageField(_('File'))
    date = models.DateTimeField(_('Date'))
    weather_conditions = models.TextField(
        _('Weather conditions'),
        max_length=350,
    )
    remarks = models.TextField(_('Remarks'), max_length=350)
    # TODO latitude, longitude, altitude, orientation ? GeoJSON Field ?

    class Meta:
        permissions = (
            ('can_read_draft_picture', 'Is able to see a draft picture'),
            ('can_change_state_picture', 'Is able to change the picture '
                                         'state'),
        )
        verbose_name = _('Picture')

        # It's our main way of sorting pictures, so it better be indexed
        indexes = [
            models.Index(fields=['point', 'created_at']),
        ]
        get_latest_by = 'created_at'


class Document(BaseUpdatableModel):
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        verbose_name=_('Owner'),
        related_name='documents',
    )
    point = models.ForeignKey(
        ObservationPoint,
        on_delete=models.PROTECT,
        verbose_name=_('Point'),
        related_name='documents',
    )
    properties = JSONField(_('Properties'), default=dict, blank=True)
    file = models.FileField(_('File'))
