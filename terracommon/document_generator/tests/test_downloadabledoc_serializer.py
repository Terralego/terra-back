import os

from django.test import TestCase
from django.urls import reverse

from terracommon.accounts.tests.factories import TerraUserFactory
from terracommon.document_generator.models import (DocumentTemplate,
                                                   DownloadableDocument)
from terracommon.document_generator.serializers import \
    DownloadableDocumentSerializer
from terracommon.trrequests.tests.factories import UserRequestFactory


class DownloadbleDocumentTestCase(TestCase):
    def setUp(self):
        template_path = os.path.join('terracommon',
                                     'document_generator',
                                     'tests',
                                     'test_template.odt')
        self.documenttemplate = DocumentTemplate.objects.create(
                                            name='test_template',
                                            documenttemplate=template_path)
        self.user = TerraUserFactory()
        self.userrequest = UserRequestFactory()
        self.downloadable_document = DownloadableDocument.objects.create(
            user=self.user,
            document=self.documenttemplate,
            linked_object=self.userrequest
        )

        self.serializer = DownloadableDocumentSerializer(
                                                    self.downloadable_document)

    def test_contain_expected_fields(self):
        data = self.serializer.data
        self.assertEqual(set(data.keys()), set(['title', 'url']))

    def test_expected_fields_content(self):
        data = self.serializer.data
        self.assertEqual(data['title'], self.documenttemplate.name)
        self.assertIn(
            reverse('document_generator:document-pdf',
                    kwargs={'request_pk': self.userrequest.pk,
                            'pk': self.documenttemplate.pk}),
            data['url'],
        )
