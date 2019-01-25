from django.urls import reverse
from rest_framework import serializers

from terracommon.accounts.mixins import UserTokenGeneratorMixin

from .models import DocumentTemplate, DownloadableDocument


class DownloadableDocumentSerializer(serializers.ModelSerializer,
                                     UserTokenGeneratorMixin):
    title = serializers.SerializerMethodField()
    url = serializers.SerializerMethodField()

    class Meta:
        model = DownloadableDocument
        fields = ('title', 'url', )

    def get_title(self, obj):
        return obj.document.name

    def get_url(self, obj):
        uidb64, token = self.get_uidb64_token_for_user(self.current_user)
        return "{}?uidb64={}&token={}".format(
            reverse('document_generator:document-pdf', kwargs={
                'request_pk': obj.linked_object.id,
                'pk': obj.document.id

            }),
            uidb64,
            token,
        )


class DocumentTemplateSerializer(serializers.ModelSerializer,
                                 UserTokenGeneratorMixin):
    url = serializers.SerializerMethodField()

    def get_url(self, obj):

        uidb64, token = self.get_uidb64_token_for_user(self.current_user)
        return "{}?uidb64={}&token={}".format(
            reverse('document_generator:document-file', kwargs={
                'pk': obj.id

            }),
            uidb64,
            token,
        )

    class Meta:
        model = DocumentTemplate
        fields = '__all__'
        extra_kwargs = {
            'documenttemplate': {'write_only': True}
        }
