from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver
from versatileimagefield.serializers import VersatileImageFieldSerializer

from .models import Viewpoint


@receiver(post_save, sender=Viewpoint)
def update_or_create_viewpoint(instance, **kwargs):
    """
    This signal is triggered after Viewpoint save (update or create). It will
    update its feature with the related viewpoint details.
    """
    point = instance.point
    point.properties = {
        'viewpoint_id': instance.id,
        'viewpoint_label': instance.label,
    }

    # Add thumbnail representation in the feature's properties
    if instance.pictures.exists():
        last_picture_sizes = VersatileImageFieldSerializer(
            'tropp'
        ).to_representation(instance.pictures.latest().file)
        point.properties['viewpoint_picture'] = last_picture_sizes['thumbnail']

    # Add any specified viewpoint property in the feature's properties
    for prop in settings.TROPP_FEATURES_PROPERTIES_FROM_VIEWPOINT:
        value = instance.properties.get(prop)
        if value is not None:
            point.properties[f'viewpoint_{prop}'] = value

    point.save()
