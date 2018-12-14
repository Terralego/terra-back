import logging

from django.contrib.contenttypes.models import ContentType
from django.core.files.uploadedfile import SimpleUploadedFile

from terracommon.datastore.models import RelatedDocument

logger = logging.getLogger(__name__)


class Base64RelatedDocumentsMixin(object):

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
