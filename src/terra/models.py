from django.contrib.postgres.fields import JSONField
from django.contrib.gis.db import models


class Layer(models.Model):
    name = models.CharField(max_length=256)


class Feature(models.Model):
    geom = models.GeometryField()
    properties = JSONField()
    layer = models.ForeignKey(Layer, on_delete=models.PROTECT)