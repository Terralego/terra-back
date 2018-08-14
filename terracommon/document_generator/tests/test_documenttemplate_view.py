import os
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
        odt_dirname = ['terracommon', 'document_generator', 'tests']
        odt_name = 'test_template.odt'
        tmp_odt = os.path.join(*odt_dirname, odt_name)

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
        self.pdf_url = 'document-pdf'

    def test_pdf_creator_method(self):
        myodt = self.myodt
        fake_userrequest = UserRequestFactory(properties=self.properties)
        DownloadableDocument.objects.create(
            user=self.user,
            document=self.myodt,
            linked_object=fake_userrequest
        )

        # Remove cache if cached
        cache_filename = (f'{myodt.documenttemplate}{myodt.name}_'
                          f'{fake_userrequest.__class__.__name__}_'
                          f'{fake_userrequest.pk}.pdf')
        cache_doc = CachedDocument(cache_filename)
        if cache_doc.is_cached():
            cache_doc.delete_cache()

        # Mock?
        DocumentGenerator.get_pdf = Mock(return_value=b'this is a PDF-1.4\n'
                                                      b'Well I think it is.')

        # Calling the Api with good params
        pks = {'request_pk': fake_userrequest.pk, 'pk': myodt.pk}
        response = self.client.post(reverse(self.pdf_url, kwargs=pks))

        self.assertEqual(status.HTTP_200_OK, response.status_code)
        self.assertEqual('application/pdf', response['Content-Type'])
        self.assertEqual(f'attachment;filename={cache_filename}',
                         response['Content-Disposition'])
        self.assertIsNotNone(response['X-Accel-Redirect'])

        DocumentGenerator.get_pdf.assert_called_with(
            fake_userrequest.properties)

    def test_pdf_creator_with_bad_requestpk(self):
        # Testing bad request_pk
        pks = {'request_pk': 999, 'pk': self.myodt.pk}
        response = self.client.post(reverse(self.pdf_url, kwargs=pks))
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
        response = self.client.post(reverse(self.pdf_url, kwargs=pks))
        self.assertEqual(status.HTTP_404_NOT_FOUND, response.status_code)

    def test_pdf_creator_without_download_pdf_permissions(self):
        userrequest = UserRequestFactory(properties=self.properties)
        pks = {'request_pk': userrequest.pk, 'pk': self.myodt.pk}
        response = self.client.post(reverse(self.pdf_url, kwargs=pks))

        self.assertEqual(status.HTTP_403_FORBIDDEN, response.status_code)

    def test_pdf_creator_with_all_pdf_permission(self):
        self._set_permissions(['can_download_all_pdf', ])
        DocumentGenerator.get_pdf = Mock(return_value=b'this is a PDF-1.4\n'
                                                      b'Well I think it is.')

        userrequest = UserRequestFactory(properties=self.properties)
        pks = {'request_pk': userrequest.pk, 'pk': self.myodt.pk}
        response = self.client.post(reverse(self.pdf_url, kwargs=pks))

        self.assertEqual(status.HTTP_200_OK, response.status_code)

    def test_pdf_creator_with_authentication(self):
        fake_userrequest = UserRequestFactory(properties=self.properties)

        # Testing unauthenticated user
        self.client.force_authenticate(user=None)
        pks = {'request_pk': fake_userrequest.pk, 'pk': self.myodt.pk}
        response = self.client.post(reverse(self.pdf_url, kwargs=pks))
        self.assertEqual(status.HTTP_401_UNAUTHORIZED, response.status_code)
