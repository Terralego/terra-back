import base64

from django.contrib.contenttypes.models import ContentType
from django.core.files.uploadedfile import SimpleUploadedFile

from terracommon.datastore.models import RelatedDocument


class Base64RelatedDocumentsMixin(object):

    def _update_or_create_documents(self, instance, documents):
        for document in documents:
            document_file = SimpleUploadedFile(
                document['key'], base64.b64decode(document.get('document')))
            RelatedDocument.objects.update_or_create(
                key=document['key'],
                object_id=instance.pk,
                content_type=ContentType.objects.get_for_model(
                                                instance.__class__),
                defaults={
                        'document': document_file,
                }
            )
