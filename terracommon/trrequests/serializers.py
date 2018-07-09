import json
import uuid

from django.db import transaction
from rest_framework import serializers

from terracommon.accounts.serializers import TerraUserSerializer
from terracommon.terra.models import Layer
from terracommon.terra.serializers import GeoJSONLayerSerializer

from .models import Comment, UserRequest


class UserRequestSerializer(serializers.ModelSerializer):
    owner = TerraUserSerializer(read_only=True)
    geojson = GeoJSONLayerSerializer(source='layer')
    reviewers = TerraUserSerializer(read_only=True, many=True)

    def create(self, validated_data):
        with transaction.atomic():
            layer = Layer.objects.create(
                    name=uuid.uuid4(),
                    schema={},
                )

            layer.from_geojson(
                json.dumps(validated_data.pop('layer')),
                '01-01',
                '12-01'
                )
            validated_data.update({
                'layer': layer,
            })

            return super().create(validated_data)

    def update(self, instance, validated_data):
        if 'layer' in validated_data:
            geojson = validated_data.pop('layer')
            instance.layer.from_geojson(json.dumps(geojson),
                                        '01-01',
                                        '12-31',
                                        update=True)
        return super().update(instance, validated_data)

    class Meta:
        model = UserRequest
        exclude = ('layer', )
        read_only_fields = ('owner', )


class CommentSerializer(serializers.ModelSerializer):
    owner = TerraUserSerializer(read_only=True)

    class Meta:
        model = Comment
        fields = '__all__'
        read_only_fields = ('owner', 'userrequest',)
