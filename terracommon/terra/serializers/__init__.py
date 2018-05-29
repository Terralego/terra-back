from django.shortcuts import get_object_or_404

from rest_framework import serializers

from terracommon.terra.models import Layer, Feature, LayerRelation, \
                                     FeatureRelation, TerraUser


class TerraUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = TerraUser
        fields = ('id', 'is_superuser', 'email', 'properties', 'is_staff',
                  'is_active')


class PropertiesSerializer(serializers.ModelSerializer):
    """
    Serialize models with a 'properties' field described by the 'schema' field
    of 'schema_model'
    The properties are dynamically flattened with other static fields.
    The viewset url must contains a parameter named against model name suffixed
    by '_pk'.
    """
    schema_model = None

    def get_fields(self):
        pk_url_kwarg = f'{self.schema_model._meta.model_name}_pk'
        schema_object = get_object_or_404(
                            self.schema_model,
                            pk=self.context['view'].kwargs[pk_url_kwarg]
                        )
        fields = super().get_fields()
        for name, description in schema_object.schema.items():
            Field = {
                'integer': serializers.IntegerField,
                'string': serializers.CharField,
            }[description['type']]
            fields.update({name: Field(source=f'properties.{name}')})
        return fields


class FeatureSerializer(PropertiesSerializer):
    schema_model = Layer

    class Meta:
        model = Feature
        fields = ('id', 'geom', 'layer', 'from_date', 'to_date', )


class FeatureInLayerSerializer(serializers.ModelSerializer):

    class Meta:
        model = Feature
        fields = ('id', 'geom', )


class LayerSerializer(serializers.ModelSerializer):

    class Meta:
        model = Layer
        fields = ('id', 'name', 'schema', 'group')


class GeoJSONLayerSerializer(serializers.JSONField):
    def to_representation(self, data):
        return data.to_geojson()


class LayerRelationSerializer(serializers.ModelSerializer):
    class Meta:
        model = LayerRelation
        fields = ('id', 'origin', 'destination', 'schema')


class FeatureRelationSerializer(PropertiesSerializer):
    schema_model = LayerRelation

    class Meta:
        model = FeatureRelation
        fields = ('id', 'origin', 'destination')
