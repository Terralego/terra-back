import os
from unittest.mock import Mock

from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient

from terracommon.accounts.tests.factories import TerraUserFactory
from terracommon.document_generator.helpers import DocumentGenerator
from terracommon.document_generator.models import DocumentTemplate
from terracommon.trrequests.tests.factories import UserRequestFactory


class DocumentTemplateViewTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = TerraUserFactory()
        self.client.force_authenticate(user=self.user)

    def test_pdf_creator_method(self):
        # Create a temporary odt
        odt_dirname = ['terracommon', 'document_generator', 'tests']
        odt_name = 'test_template.odt'
        tmp_odt = os.path.join(*odt_dirname, odt_name)

        # Store it in the database
        myodt = DocumentTemplate.objects.create(name='testodt',
                                                template=tmp_odt)

        # Create a fake UserRequest
        fake_properties = {
            'from': '01/01/2018',
            'to': '31/12/2018',
            'registration': 'AS-AS-AA-AS-AS',
            'authorization': 'okay'
        }
        fake_userrequest = UserRequestFactory(owner=self.user,
                                              properties=fake_properties)

        # Mock?
        DocumentGenerator.get_pdf = Mock(return_value=b'this is a PDF-1.4\n'
                                                      b'Well I think it is.')

        # Calling the Api with good params
        url_name = 'document-pdf'
        pks = {'request_pk': fake_userrequest.pk, 'pk': myodt.pk}
        response = self.client.post(reverse(url_name, kwargs=pks))

        self.assertEqual(200, response.status_code)

        DocumentGenerator.get_pdf.assert_called_with(
            fake_userrequest.properties)

        pdf_header = response.content.split(b'\n')[0]
        self.assertIn(b'PDF', pdf_header)

        # Testing bad request_pk
        pks_bad_requestpk = {'request_pk': 999, 'pk': myodt.pk}
        response_404 = self.client.post(reverse(url_name,
                                                kwargs=pks_bad_requestpk))
        self.assertEqual(404, response_404.status_code)

        # Testing bad pk
        pks_bad_pk = {'request_pk': fake_userrequest.pk, 'pk': 9999}
        response_404 = self.client.post(reverse(url_name,
                                                kwargs=pks_bad_pk))
        self.assertEqual(404, response_404.status_code)

        # Testing authenticated user without permissions
        userrequest_403 = UserRequestFactory(properties=fake_properties)
        pks_no_permissions = {'request_pk': userrequest_403.pk, 'pk': myodt.pk}

        response_403 = self.client.post(reverse(url_name,
                                                kwargs=pks_no_permissions))
        self.assertEqual(403, response_403.status_code)

        # Testing unauthenticated user
        self.client.force_authenticate(user=None)
        response_401 = self.client.post(reverse(url_name, kwargs=pks))
        self.assertEqual(401, response_401.status_code)
