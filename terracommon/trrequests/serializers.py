import json
import uuid

from django.db import transaction
from rest_framework import serializers

from terracommon.terra.models import Layer
from terracommon.terra.serializers import (LayerWithFeaturesSerializer,
                                           TerraUserSerializer)

from .models import Comment, Organization, UserRequest


class UserRequestSerializer(serializers.ModelSerializer):
    owner = TerraUserSerializer(read_only=True)
    geojson = LayerWithFeaturesSerializer(source='layer')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        request_user = self.context['request'].user
        self.fields['organization'].queryset = (
                            Organization.objects.filter(owner=request_user))

    def create(self, validated_data):
        with transaction.atomic():
            layer = Layer.objects.create(
                    name=uuid.uuid4(),
                    schema={},
                )

            layer.from_geojson(
                json.dumps(validated_data.pop('layer').get('geojson')),
                '01-01',
                '12-01'
                )
            validated_data.update({
                'layer': layer,
            })

            return super().create(validated_data)

    def update(self, instance, validated_data):
        geojson = validated_data.pop('layer').get('geojson')
        instance.layer.from_geojson(json.dumps(geojson),
                                    '01-01',
                                    '12-31',
                                    True)
        return super().update(instance, validated_data)

    class Meta:
        model = UserRequest
        exclude = ('layer', )
        read_only_fields = ('owner', )


class OrganizationSerializer(serializers.ModelSerializer):

    class Meta:
        model = Organization
        fields = '__all__'
        read_only_fields = ('owner', )


class CommentSerializer(serializers.ModelSerializer):
    owner = TerraUserSerializer(read_only=True)

    class Meta:
        model = Comment
        fields = '__all__'
        read_only_fields = ('owner', 'userrequest',)
