import base64
import binascii
import logging

from django.contrib.contenttypes.models import ContentType
from django.core.files.uploadedfile import SimpleUploadedFile

from terracommon.datastore.models import RelatedDocument

logger = logging.getLogger(__name__)


class Base64RelatedDocumentsMixin(object):

    def _update_or_create_documents(self, instance, documents):
        for document in documents:
            try:
                encoded = document.get('document', ',').split(",", 1)[1]

            # Caught the error to log it then re-raised it
            except IndexError:
                logger.warning(
                    f"cannot read document {document.get('document')}"
                )
                raise
            else:
                try:
                    document_file = SimpleUploadedFile(
                        document['key'], base64.b64decode(encoded))

                # Caught the error to log it then re-raised it
                except binascii.Error:
                    logger.warning(f'{document} is not a base64 format')
                    raise
                else:
                    RelatedDocument.objects.update_or_create(
                        key=document['key'],
                        object_id=instance.pk,
                        content_type=ContentType.objects.get_for_model(
                                                        instance.__class__),
                        defaults={
                                'document': document_file,
                        }
                    )
