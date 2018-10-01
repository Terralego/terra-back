import os
from datetime import date
from tempfile import NamedTemporaryFile
from unittest.mock import MagicMock, patch

from django.conf import settings
from django.test import TestCase
from django.urls import reverse
from jinja2 import TemplateSyntaxError
from requests import ConnectionError, HTTPError
from rest_framework import status
from rest_framework.test import APIClient

from terracommon.accounts.tests.factories import TerraUserFactory
from terracommon.document_generator.helpers import DocumentGenerator
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

        with patch.object(DocumentGenerator,
                          'get_pdf',
                          return_value=fake_pdf.name) as mock_dg:

            # Expected name schema
            pdf_name = f'document_{date.today()}.pdf'

            # Testing with no MEDIA_ACCEL_REDIRECT
            response = self.client.get(reverse(self.pdfcreator_urlname,
                                               kwargs=pks))
            self.assertEqual(status.HTTP_200_OK, response.status_code)
            self.assertEqual('application/pdf', response['Content-Type'])
            self.assertEqual(f'attachment;filename={pdf_name}',
                             response['Content-Disposition'])

            self.assertEqual(response.content, fake_pdf.read())

            mock_dg.assert_called_with(data=fake_userrequest)

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

        fake_pdf = NamedTemporaryFile(mode='wb+',
                                      delete=False,
                                      dir='./')
        fake_pdf.write(b'Header PDF-1.4\nsome line.')

        with patch.object(
                DocumentGenerator,
                'get_pdf',
                return_value=os.path.basename(fake_pdf.name)) as mock_dg:
            # Expected name schema
            pdf_name = f'document_{date.today()}.pdf'
            with self.settings(MEDIA_ACCEL_REDIRECT=True):
                response = self.client.get(reverse(self.pdfcreator_urlname,
                                                   kwargs=pks))

                self.assertEqual(status.HTTP_200_OK, response.status_code)
                self.assertEqual('application/pdf', response['Content-Type'])
                self.assertEqual(f'attachment;filename={pdf_name}',
                                 response['Content-Disposition'])
                self.assertIn(settings.MEDIA_URL,
                              response.get('X-Accel-Redirect'))
                mock_dg.assert_called_with(data=userrequest)

        os.remove(fake_pdf.name)

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

        with patch.object(DocumentGenerator,
                          'get_pdf',
                          return_value=fake_pdf.name) as mock_dg:
            userrequest = UserRequestFactory(properties=self.properties)
            pks = {'request_pk': userrequest.pk, 'pk': self.myodt.pk}

            response = self.client.get(reverse(self.pdfcreator_urlname,
                                               kwargs=pks))

            self.assertEqual(status.HTTP_200_OK, response.status_code)
            mock_dg.assert_called_with(data=userrequest)

        os.remove(fake_pdf.name)

    def test_pdf_creator_with_authentication(self):
        fake_userrequest = UserRequestFactory(properties=self.properties)

        # Testing unauthenticated user
        self.client.force_authenticate(user=None)
        pks = {'request_pk': fake_userrequest.pk, 'pk': self.myodt.pk}

        response = self.client.get(reverse(self.pdfcreator_urlname,
                                           kwargs=pks))
        self.assertEqual(status.HTTP_401_UNAUTHORIZED, response.status_code)

        # Reseting default test settings
        self.client.force_authenticate(user=self.user)

    def test_raises_filenotfounderror_return_404(self):
        ur = UserRequestFactory()
        pks = {'request_pk': ur.pk, 'pk': self.myodt.pk}

        # Creating Permission
        DownloadableDocument.objects.create(user=self.user,
                                            document=self.myodt,
                                            linked_object=ur)
        # Mocking getpdf
        DocumentGenerator.get_pdf = MagicMock(side_effect=FileNotFoundError)

        response = self.client.get(reverse(self.pdfcreator_urlname,
                                           kwargs=pks))
        self.assertEqual(status.HTTP_404_NOT_FOUND, response.status_code)

    def test_raises_HTTPError_return_503(self):
        ur = UserRequestFactory()
        pks = {'request_pk': ur.pk, 'pk': self.myodt.pk}

        # Creating Permission
        DownloadableDocument.objects.create(user=self.user,
                                            document=self.myodt,
                                            linked_object=ur)
        # Mocking getpdf
        DocumentGenerator.get_pdf = MagicMock(side_effect=HTTPError)

        response = self.client.get(reverse(self.pdfcreator_urlname,
                                           kwargs=pks))
        self.assertEqual(status.HTTP_503_SERVICE_UNAVAILABLE,
                         response.status_code)

    def test_raises_ConnectionError_return_503(self):
        ur = UserRequestFactory()
        pks = {'request_pk': ur.pk, 'pk': self.myodt.pk}

        # Creating Permission
        DownloadableDocument.objects.create(user=self.user,
                                            document=self.myodt,
                                            linked_object=ur)
        # Mocking getpdf
        DocumentGenerator.get_pdf = MagicMock(side_effect=ConnectionError)
        response = self.client.get(reverse(self.pdfcreator_urlname,
                                           kwargs=pks))
        self.assertEqual(status.HTTP_503_SERVICE_UNAVAILABLE,
                         response.status_code)

    def test_raises_TemplateSyntaxError_return_500(self):
        ur = UserRequestFactory()
        pks = {'request_pk': ur.pk, 'pk': self.myodt.pk}

        # Creating Permission
        DownloadableDocument.objects.create(user=self.user,
                                            document=self.myodt,
                                            linked_object=ur)
        # Mocking getpdf
        DocumentGenerator.get_pdf = MagicMock(side_effect=TemplateSyntaxError(
                                                message='error',
                                                lineno=1))
        response = self.client.get(reverse(self.pdfcreator_urlname,
                                           kwargs=pks))
        self.assertEqual(status.HTTP_500_INTERNAL_SERVER_ERROR,
                         response.status_code)
