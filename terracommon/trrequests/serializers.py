import json
import logging
import uuid

from django.contrib.contenttypes.models import ContentType
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import transaction
from django.urls import reverse
from geostore.models import Layer
from geostore.serializers import GeoJSONLayerSerializer
from rest_framework import serializers

from terracommon.accounts.mixins import UserTokenGeneratorMixin
from terracommon.accounts.serializers import TerraUserSerializer
from terracommon.core.mixins import SerializerCurrentUserMixin
from terracommon.datastore.models import RelatedDocument
from terracommon.datastore.serializers import (RelatedDocumentPDFSerializer,
                                               RelatedDocumentSerializer)
from terracommon.document_generator.serializers import \
    DownloadableDocumentSerializer
from terracommon.events.signals import event

from .models import Comment, UserRequest

logger = logging.getLogger(__name__)


class UserRequestSerializer(serializers.ModelSerializer, SerializerCurrentUserMixin):
    owner = TerraUserSerializer(read_only=True)
    geojson = GeoJSONLayerSerializer(source='layer')
    reviewers = TerraUserSerializer(read_only=True, many=True)
    has_new_comments = serializers.SerializerMethodField()
    has_new_changes = serializers.SerializerMethodField()
    downloadables = DownloadableDocumentSerializer(read_only=True,
                                                   many=True,
                                                   source='downloadable')
    documents = RelatedDocumentSerializer(many=True, required=False)

    def create(self, validated_data):
        with transaction.atomic():

            layer = json.dumps(validated_data.pop('layer', {}))
            validated_data.update({
                'layer': self._create_layer(layer),
            })
            documents = validated_data.pop('documents', [])
            instance = super().create(validated_data)
            self._update_or_create_documents(instance, documents)

            try:
                instance.user_read(self.current_user)
            except AttributeError:
                logger.info('Cannot set object read since current_user is '
                            'unknown')
            return instance

    def _create_layer(self, layer_json):
        layer = Layer.objects.create(
            name=uuid.uuid4(),
            schema={},
        )

        layer.from_geojson(
            layer_json,
        )

        return layer

    def update(self, instance, validated_data):
        old_properties, old_state = instance.properties, instance.state

        if 'layer' in validated_data:
            geojson = validated_data.pop('layer')
            instance.layer.from_geojson(json.dumps(geojson), update=True)

        documents = validated_data.pop('documents', [])
        instance = super().update(instance, validated_data)
        self._update_or_create_documents(instance, documents)

        if ('state' in validated_data
                and old_state != validated_data['state']):
            event.send(
                self.__class__,
                action="USERREQUEST_STATE_CHANGED",
                user=self.context['request'].user,
                instance=instance,
                old_state=old_state)

        if ('properties' in validated_data
                and old_properties != validated_data['properties']):
            event.send(sender=self.__class__,
                       action='USERREQUEST_PROPERTIES_CHANGED',
                       user=self.context['request'].user,
                       instance=instance,
                       old_properties=old_properties)

        try:
            instance.user_read(self.current_user)
        except AttributeError:
            logger.info('Cannot set object read since current_user is '
                        'unknown')
        return instance

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

    def _update_or_create_documents(self, instance, documents):
        for document in documents:
            RelatedDocument.objects.update_or_create(
                key=document['key'],
                object_id=instance.pk,
                content_type=ContentType.objects.get_for_model(
                                                instance.__class__),
                defaults={
                    'document': SimpleUploadedFile(document['key'],
                                                   document['document']),
                }
            )

    class Meta:
        model = UserRequest
        exclude = ('layer',)
        read_only_fields = ('owner', 'expiry', )


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
            reverse('trrequests:comment-attachment',
                    args=[obj.userrequest_id, obj.pk]),
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
                    json.dumps(validated_data.pop('layer'))
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

    class Meta:
        model = Comment
        fields = '__all__'
        read_only_fields = ('owner', 'userrequest')
        extra_kwargs = {
            'attachment': {'write_only': True}
        }


class UserRequestPDFSerializer(UserRequestSerializer):
    documents = RelatedDocumentPDFSerializer(many=True, required=False)
