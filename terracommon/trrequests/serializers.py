import json
import uuid

from django.db import transaction
from rest_framework import serializers

from terracommon.terra.models import Layer

from .models import Comment, Organization, UserRequest


class UserRequestSerializer(serializers.ModelSerializer):
    layer = serializers.ModelField(
        model_field=UserRequest._meta.get_field('layer'),
        read_only=True)
    geojson = serializers.JSONField(write_only=True, required=True)

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

            layer.from_geojson(json.dumps(validated_data.pop('geojson')))
            validated_data.update({
                'layer': layer,
            })

            return super().create(validated_data)

    class Meta:
        model = UserRequest
        fields = '__all__'
        read_only_fields = ('owner', )


class OrganizationSerializer(serializers.ModelSerializer):

    class Meta:
        model = Organization
        fields = '__all__'
        read_only_fields = ('owner', )


class CommentSerializer(serializers.ModelSerializer):

    class Meta:
        model = Comment
        fields = '__all__'
        read_only_fields = ('owner', 'userrequest',)
