from django.conf import settings
from django.contrib.contenttypes.fields import GenericRelation
from django.contrib.gis.db import models
from django.contrib.postgres.fields import JSONField
from django.utils.translation import ugettext_lazy as _
from geostore.models import Feature
from versatileimagefield.fields import VersatileImageField

from terracommon.core.mixins import BaseUpdatableModel
from terracommon.core.settings import STATES


class BaseLabelModel(BaseUpdatableModel):
    label = models.CharField(_('Label'), max_length=100)

    class Meta:
        abstract = True

    def __str__(self):
        return self.label


class ViewpointsManager(models.Manager):
    def with_accepted_pictures(self):
        return super().get_queryset().filter(
            pictures__state=settings.STATES.ACCEPTED,
        ).distinct()


class Viewpoint(BaseLabelModel):
    point = models.ForeignKey(
        Feature,
        on_delete=models.CASCADE,
        related_name='points',
    )
    properties = JSONField(_('Properties'), default=dict, blank=True)
    related = GenericRelation('datastore.RelatedDocument')

    objects = ViewpointsManager()

    @property
    def status(self):
        """
        Return the status of this viewpoint for a campaign
        :param self:
        :return: string (missing, draft, submitted, accepted)
        """
        # Get only pictures created for the campaign
        picture = self.pictures.latest()
        if picture.created_at < self.created_at:
            return settings.STATES.CHOICES_DICT[settings.STATES.MISSING]
        return STATES.CHOICES_DICT[picture.state]

    class Meta:
        permissions = (
            ('can_download_pdf', 'Is able to download a pdf document'),
        )
        ordering = ['-created_at']


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

    @property
    def statistics(self):
        queryset = self.viewpoints.annotate(
            missing=models.Count('pk', filter=models.Q(
                pictures__isnull=True
            )),
            pending=models.Count('pictures', filter=models.Q(
                pictures__state=STATES.DRAFT
            )),
            refused=models.Count('pictures', filter=models.Q(
                pictures__state=STATES.REFUSED
            )),
        ).values('missing', 'pending', 'refused')
        try:
            return queryset[0]
        except IndexError:
            return {'missing': 0, 'pending': 0, 'refused': 0}

    @property
    def status(self):
        return not self.viewpoints.exclude(
            pictures__state=STATES.ACCEPTED,
        ).exists()

    class Meta:
        permissions = (
            ('manage_all_campaigns', "Can manage all campaigns"),
        )
        ordering = ['-created_at']


class Picture(BaseUpdatableModel):
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        verbose_name=_('Owner'),
        related_name='pictures',
    )
    viewpoint = models.ForeignKey(
        Viewpoint,
        on_delete=models.CASCADE,
        related_name='pictures',
    )
    # States may be : draft, metadata_ok (submitted), accepted, refused
    state = models.IntegerField(_('State'), default=STATES.DRAFT)

    properties = JSONField(_('Properties'), default=dict, blank=True)
    file = VersatileImageField(_('File'))

    # Different from created_at which is the upload date
    date = models.DateTimeField(_('Date'))

    # TODO maybe move that to another model with GenericFK?
    remarks = models.TextField(_('Remarks'), max_length=350)

    class Meta:
        permissions = (
            ('change_state_picture', 'Is able to change the picture '
                                     'state'),
        )
        # It's our main way of sorting pictures, so it better be indexed
        indexes = [
            models.Index(fields=['viewpoint', 'date']),
        ]
        get_latest_by = 'date'
        ordering = ['-date']

    def save(self, *args, **kwargs):
        if not settings.TROPP_PICTURES_STATES_WORKFLOW:
            self.state = settings.STATES.ACCEPTED
        super().save(*args, **kwargs)
