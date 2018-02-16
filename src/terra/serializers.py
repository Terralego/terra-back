from copy import copy

from django.shortcuts import get_object_or_404

from rest_framework import serializers

from .models import Layer, Feature, FeatureRelation


class LayerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Layer
        fields = ('id', 'name', 'schema')


class FeatureSerializer(serializers.ModelSerializer):
    class Meta:
        model = Feature
        fields = ('id', 'geom', 'layer')

    def get_fields(self):
        layer = get_object_or_404(Layer, pk=self.context['view'].kwargs['layer_pk'])
        fields = super().get_fields()
        for name, description in layer.schema.items():
            Field = {
                'integer': serializers.IntegerField,
                'string': serializers.CharField,
            }[description['type']]
            fields.update({name: Field(source=f'properties.{name}')})
        return fields


class FeatureRelationSerializer(serializers.ModelSerializer):
    class Meta:
        model = FeatureRelation
        fields = ('id', 'origin', 'destination', 'properties')
