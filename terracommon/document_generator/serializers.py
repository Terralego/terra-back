from django.urls import reverse
from rest_framework import serializers

from .models import DownloadableDocument


class DownloadableDocumentSerializer(serializers.ModelSerializer):
    title = serializers.SerializerMethodField()
    url = serializers.SerializerMethodField()

    class Meta:
        model = DownloadableDocument
        fields = ('title', 'url', )

    def get_title(self, obj):
        return obj.document.name

    def get_url(self, obj):
        return reverse('document-pdf',
                       kwargs={
                           'request_pk': obj.linked_object.id,
                           'pk': obj.document.id})
