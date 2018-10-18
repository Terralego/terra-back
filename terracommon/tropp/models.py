from django.conf import settings
from django.contrib.postgres.fields import JSONField
from django.db import models

from terracommon.core.mixins import BaseUpdatableModel
from terracommon.terra.models import Layer


class ObservationPoint(BaseUpdatableModel):
    label = models.CharField()
    owner = models.ForeignKey(settings.AUTH_USER_MODEL,
                              on_delete=models.PROTECT,
                              related_name='observation_points')
    layer = models.ForeignKey(Layer,
                              on_delete=models.PROTECT,
                              related_name='observation_points')
    properties = JSONField(default=dict, blank=True)

    def __str__(self):
        return self.label

    class Meta:
        permissions = (
            ('can_create_points', 'Is able to create a new observation point'),
            ('can_download_pdf', 'Is able to download a pdf document'),
        )


class Picture(BaseUpdatableModel):
    owner = models.ForeignKey(settings.AUTH_USER_MODEL,
                              on_delete=models.PROTECT,
                              related_name='pictures')
    point = models.ForeignKey(ObservationPoint,
                              on_delete=models.PROTECT,
                              related_name='pictures')
    state = models.IntegerField(default=settings.STATES.DRAFT)
    properties = JSONField(default=dict, blank=True)

    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        permissions = (
            ('can_create_picture', 'Is able to create a new picture'),
            ('can_read_draft_picture', 'Is able to see a draft picture'),
            ('can_change_state_picture',
             'Is able to change the picture state'),
        )

        # It's our main way of sorting pictures, so it better be indexed
        indexes = [
            models.Index(fields=['point', 'created_at']),
        ]
        get_latest_by = "created_at"
