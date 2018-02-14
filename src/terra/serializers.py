from rest_framework import serializers

from .models import Layer, Feature


class LayerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Layer
        fields = ('id', 'name')


class FeatureSerializer(serializers.ModelSerializer):
    class Meta:
        model = Feature
        fields = ('id', 'geom', 'properties', 'layer')
