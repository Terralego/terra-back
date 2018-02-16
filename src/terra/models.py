from django.contrib.postgres.fields import JSONField
from django.contrib.gis.db import models


class Layer(models.Model):
    name = models.CharField(max_length=256)
    schema = JSONField(default=dict, blank=True)


class Feature(models.Model):
    geom = models.GeometryField()
    properties = JSONField()
    layer = models.ForeignKey(Layer, on_delete=models.PROTECT)


class FeatureRelation(models.Model):
    origin = models.ForeignKey(Feature, on_delete=models.PROTECT, related_name='relations_as_origin')
    destination = models.ForeignKey(Feature, on_delete=models.PROTECT, related_name='relations_as_destination')
    properties = JSONField(default=dict, blank=True)
