import logging

from rest_framework import serializers

from .models import DataStore, RelatedDocument

logger = logging.getLogger(__name__)


class DataStoreSerializer(serializers.ModelSerializer):
    class Meta:
        model = DataStore
        fields = '__all__'
        read_only_fields = ('key', )


class RelatedDocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = RelatedDocument
        fields = ('key', 'model_object', 'document')
