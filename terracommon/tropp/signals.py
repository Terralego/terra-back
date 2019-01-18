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
    if instance.pictures.exists():
        last_picture_representation = VersatileImageFieldSerializer(
            'tropp'
        ).to_representation(instance.pictures.latest().file)
        # We don't need those two representation in the feature's properties
        del last_picture_representation['original']
        del last_picture_representation['full']
        point.properties['viewpoint_picture'] = last_picture_representation

    point.save()
