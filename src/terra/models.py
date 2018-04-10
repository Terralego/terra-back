import json

from django.contrib.postgres.fields import JSONField
from django.contrib.gis.db import models
from django.contrib.gis.geos.geometry import GEOSGeometry


class Layer(models.Model):
    name = models.CharField(max_length=256)
    schema = JSONField(default=dict, blank=True)

    def import_geojson(self, geojson_file):
        geojson = json.loads(geojson_file.read())
        for feature in geojson.get('features', []):
            Feature.objects.create(
                layer=self,
                properties=feature.get('properties', {}),
                geom=GEOSGeometry(json.dumps(feature.get('geometry')))
            )


class Feature(models.Model):
    geom = models.GeometryField()
    properties = JSONField()
    layer = models.ForeignKey(Layer, on_delete=models.PROTECT)


class LayerRelation(models.Model):
    origin = models.ForeignKey(Layer, on_delete=models.PROTECT, related_name='relations_as_origin')
    destination = models.ForeignKey(Layer, on_delete=models.PROTECT, related_name='relations_as_destination')
    schema = JSONField(default=dict, blank=True)


class FeatureRelation(models.Model):
    origin = models.ForeignKey(Feature, on_delete=models.PROTECT, related_name='relations_as_origin')
    destination = models.ForeignKey(Feature, on_delete=models.PROTECT, related_name='relations_as_destination')
    properties = JSONField(default=dict, blank=True)
