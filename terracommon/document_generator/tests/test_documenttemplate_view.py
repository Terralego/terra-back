import os
from tempfile import NamedTemporaryFile
from unittest.mock import Mock

from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from terracommon.accounts.tests.factories import TerraUserFactory
from terracommon.document_generator.helpers import (CachedDocument,
                                                    DocumentGenerator)
from terracommon.document_generator.models import (DocumentTemplate,
                                                   DownloadableDocument)
from terracommon.trrequests.tests.factories import UserRequestFactory
from terracommon.trrequests.tests.mixins import TestPermissionsMixin


class DocumentTemplateViewTestCase(TestCase, TestPermissionsMixin):
    def setUp(self):
        self.client = APIClient()
        self.user = TerraUserFactory()
        self.client.force_authenticate(user=self.user)

        # get testing template
        tmp_odt = os.path.join('terracommon',
                               'document_generator',
                               'tests',
                               'test_template.odt')

        # Store it in the database
        DocumentTemplate.objects.create(name='testodt',
                                        documenttemplate=tmp_odt)
        self.myodt = DocumentTemplate.objects.get(name='testodt')

        # Create a fake UserRequest
        self.properties = {
            'from': '01/01/2018',
            'to': '31/12/2018',
            'registration': 'AS-AS-AA-AS-AS',
            'authorization': 'okay'
        }
        self.pdfcreator_urlname = 'document-pdf'

    def test_pdf_creator_method_with_dev_settings(self):
        fake_userrequest = UserRequestFactory(properties=self.properties)
        pks = {'request_pk': fake_userrequest.pk, 'pk': self.myodt.pk}

        # Create permissions
        DownloadableDocument.objects.create(
            user=self.user,
            document=self.myodt,
            linked_object=fake_userrequest
        )

        # Mocking
        fake_pdf = NamedTemporaryFile(mode='wb+', delete=False)
        fake_pdf.write(b'Header PDF-1.4\nsome line.')
        DocumentGenerator.get_pdf = Mock(
            return_value=CachedDocument(fake_pdf.name))

        # Testing with no MEDIA_ACCEL_REDIRECT
        response = self.client.get(reverse(self.pdfcreator_urlname,
                                           kwargs=pks))
        self.assertEqual(status.HTTP_200_OK, response.status_code)
        self.assertEqual('application/pdf', response['Content-Type'])
        self.assertEqual(f'attachment;filename={fake_pdf.name}',
                         response['Content-Disposition'])

        DocumentGenerator.get_pdf.assert_called_with(
            data=fake_userrequest)

        with open(fake_pdf.name, 'rb') as pdf:
            self.assertEqual(response.content, pdf.read())

        os.remove(fake_pdf.name)

    def test_pdf_creator_method_with_prod_settings(self):
        userrequest = UserRequestFactory(properties=self.properties)
        pks = {'request_pk': userrequest.pk, 'pk': self.myodt.pk}

        # Create permissions
        DownloadableDocument.objects.create(
            user=self.user,
            document=self.myodt,
            linked_object=userrequest
        )

        fake_pdf = NamedTemporaryFile(mode='wb+', delete=False)
        fake_pdf.write(b'Header PDF-1.4\nsome line.')
        DocumentGenerator.get_pdf = Mock(
            return_value=CachedDocument(fake_pdf.name))

        with self.settings(MEDIA_ACCEL_REDIRECT=True):
            response = self.client.get(reverse(self.pdfcreator_urlname,
                                               kwargs=pks))
            self.assertEqual(status.HTTP_200_OK, response.status_code)
            self.assertEqual('application/pdf', response['Content-Type'])
            self.assertEqual(f'attachment;filename={fake_pdf.name}',
                             response['Content-Disposition'])

            DocumentGenerator.get_pdf.assert_called_with(
                data=userrequest)

            cached_doc = CachedDocument(fake_pdf.name)
            self.assertEqual(response.get('X-Accel-Redirect'),
                             cached_doc.url)
            cached_doc.close()
            cached_doc.remove()
            self.assertFalse(os.path.isfile(cached_doc.name))

    def test_pdf_creator_with_bad_requestpk(self):
        # Testing bad request_pk
        pks = {'request_pk': 999, 'pk': self.myodt.pk}

        response = self.client.get(reverse(self.pdfcreator_urlname,
                                           kwargs=pks))
        self.assertEqual(status.HTTP_404_NOT_FOUND, response.status_code)

    def test_pdf_creator_with_bad_pk(self):
        fake_userrequest = UserRequestFactory(properties=self.properties)
        DownloadableDocument.objects.create(
            user=self.user,
            document=self.myodt,
            linked_object=fake_userrequest
        )
        # Testing bad pk
        pks = {'request_pk': fake_userrequest.pk, 'pk': 9999}

        response = self.client.get(reverse(self.pdfcreator_urlname,
                                           kwargs=pks))
        self.assertEqual(status.HTTP_404_NOT_FOUND, response.status_code)

    def test_pdf_creator_without_download_pdf_permissions(self):
        userrequest = UserRequestFactory(properties=self.properties)
        pks = {'request_pk': userrequest.pk, 'pk': self.myodt.pk}

        response = self.client.get(reverse(self.pdfcreator_urlname,
                                           kwargs=pks))

        self.assertEqual(status.HTTP_404_NOT_FOUND, response.status_code)

    def test_pdf_creator_with_all_pdf_permission(self):
        self._set_permissions(['can_download_all_pdf', ])

        fake_pdf = NamedTemporaryFile(mode='wb+',
                                      delete=False)
        fake_pdf.write(b'Header PDF-1.4\nsome line.')
        DocumentGenerator.get_pdf = Mock(
            return_value=CachedDocument(fake_pdf.name))

        userrequest = UserRequestFactory(properties=self.properties)
        pks = {'request_pk': userrequest.pk, 'pk': self.myodt.pk}

        response = self.client.get(reverse(self.pdfcreator_urlname,
                                           kwargs=pks))

        self.assertEqual(status.HTTP_200_OK, response.status_code)

        DocumentGenerator.get_pdf.assert_called_with(
            data=userrequest)

        os.remove(fake_pdf.name)

    def test_pdf_creator_with_authentication(self):
        fake_userrequest = UserRequestFactory(properties=self.properties)

        # Testing unauthenticated user
        self.client.force_authenticate(user=None)
        pks = {'request_pk': fake_userrequest.pk, 'pk': self.myodt.pk}

        response = self.client.get(reverse(self.pdfcreator_urlname,
                                           kwargs=pks))
        self.assertEqual(status.HTTP_401_UNAUTHORIZED, response.status_code)
