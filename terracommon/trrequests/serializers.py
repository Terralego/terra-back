import json
import logging
import uuid

from django.db import transaction
from django.urls import reverse
from django.utils.functional import cached_property
from rest_framework import serializers

from terracommon.accounts.mixins import UserTokenGeneratorMixin
from terracommon.accounts.serializers import TerraUserSerializer
from terracommon.events.signals import event
from terracommon.terra.models import Layer
from terracommon.terra.serializers import GeoJSONLayerSerializer

from .models import Comment, UserRequest

logger = logging.getLogger(__name__)


class UserRequestSerializer(serializers.ModelSerializer):
    owner = TerraUserSerializer(read_only=True)
    geojson = GeoJSONLayerSerializer(source='layer')
    reviewers = TerraUserSerializer(read_only=True, many=True)
    has_new_comments = serializers.SerializerMethodField()
    has_new_changes = serializers.SerializerMethodField()

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

            instance = super().create(validated_data)
            try:
                instance.user_read(self.current_user)
            except AttributeError:
                logger.info('Cannot set object read since current_user is '
                            'unknown')
            return instance

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

        try:
            instance.user_read(self.current_user)
        except AttributeError:
            logger.info('Cannot set object read since current_user is '
                        'unknown')
        return instance

    @cached_property
    def current_user(self):
        return (self.context['request'].user
                if 'request' in self.context else None)

    def get_has_new_comments(self, obj):
        read = obj.get_user_read(self.current_user)
        last_comment = obj.get_comments_for_user(
            self.current_user).order_by('-updated_at').first()

        if read is None and last_comment is not None:
            return True

        return (last_comment is not None
                and (read.last_read < last_comment.updated_at))

    def get_has_new_changes(self, obj):
        read = obj.get_user_read(self.current_user)

        return read is None or (read.last_read < obj.updated_at)

    class Meta:
        model = UserRequest
        exclude = ('layer',)
        read_only_fields = ('owner', 'expiry')


class CommentSerializer(serializers.ModelSerializer,
                        UserTokenGeneratorMixin):
    owner = TerraUserSerializer(read_only=True)
    attachment_url = serializers.SerializerMethodField()
    geojson = GeoJSONLayerSerializer(source='layer', required=False)

    def get_attachment_url(self, obj):
        uidb64, token = self.get_uidb64_token_for_user(self.current_user)

        if not obj.attachment:
            return None

        return "{}?uidb64={}&token={}".format(
            reverse('comment-attachment', args=[obj.userrequest_id, obj.pk]),
            uidb64,
            token)

    def create(self, validated_data):

        with transaction.atomic():
            if 'layer' in validated_data:
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

            instance = super().create(validated_data)
            try:
                instance.userrequest.user_read(self.context['request'].user)
            except AttributeError:
                logger.info('Cannot set object read since current_user is '
                            'unknown')
            return instance

    @cached_property
    def current_user(self):
        return (self.context['request'].user
                if 'request' in self.context else None)

    class Meta:
        model = Comment
        fields = '__all__'
        read_only_fields = ('owner', 'userrequest')
        extra_kwargs = {
            'attachment': {'write_only': True}
        }
