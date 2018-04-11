import json

from django.contrib.postgres.fields import JSONField
from django.contrib.gis.db import models
from django.contrib.gis.geos.geometry import GEOSGeometry

from django.core.serializers import serialize


class Layer(models.Model):
    name = models.CharField(max_length=256)
    schema = JSONField(default=dict, blank=True)

    def from_geojson(self, geojson_data):
        """
        Import geojson raw data in a layer
        Args:
            geojson_data(str): must be raw text json data
        """
        geojson = json.loads(geojson_data)
        for feature in geojson.get('features', []):
            Feature.objects.create(
                layer=self,
                properties=feature.get('properties', {}),
                geom=GEOSGeometry(json.dumps(feature.get('geometry')))
            )

    def to_geojson(self):
        return json.loads(serialize('geojson',
                         self.features.all(),
                         fields=('properties',),
                         geometry_field='geom',
                         properties_field='properties'))


class Feature(models.Model):
    geom = models.GeometryField()
    properties = JSONField()
    layer = models.ForeignKey(Layer, on_delete=models.PROTECT, related_name='features')


class LayerRelation(models.Model):
    origin = models.ForeignKey(Layer, on_delete=models.PROTECT, related_name='relations_as_origin')
    destination = models.ForeignKey(Layer, on_delete=models.PROTECT, related_name='relations_as_destination')
    schema = JSONField(default=dict, blank=True)


class FeatureRelation(models.Model):
    origin = models.ForeignKey(Feature, on_delete=models.PROTECT, related_name='relations_as_origin')
    destination = models.ForeignKey(Feature, on_delete=models.PROTECT, related_name='relations_as_destination')
    properties = JSONField(default=dict, blank=True)
