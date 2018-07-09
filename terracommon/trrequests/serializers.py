import json
import uuid

from django.db import transaction
from django.urls import reverse
from rest_framework import serializers

from terracommon.accounts.serializers import TerraUserSerializer
from terracommon.events.signals import event
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
        old_state = instance.state

        if 'layer' in validated_data:
            geojson = validated_data.pop('layer')
            instance.layer.from_geojson(json.dumps(geojson),
                                        '01-01',
                                        '12-31',
                                        update=True)

        instance = super().update(instance, validated_data)

        if ('state' in validated_data
                and old_state != validated_data['state']):
            event.send(
                self.__class__,
                action="USERREQUEST_STATE_CHANGED",
                user=self.context['request'].user,
                instance=instance,
                old_state=old_state)

        return instance

    class Meta:
        model = UserRequest
        exclude = ('layer',)
        read_only_fields = ('owner',)


class CommentSerializer(serializers.ModelSerializer):
    owner = TerraUserSerializer(read_only=True)

    def to_representation(self, obj):
        repr = super(CommentSerializer, self).to_representation(obj)
        if repr.get('attachment'):
            repr['attachment'] = reverse('comment-attachment',
                                         args=[obj.userrequest_id, obj.pk])
        return repr

    class Meta:
        model = Comment
        fields = '__all__'
        read_only_fields = ('owner', 'userrequest')
