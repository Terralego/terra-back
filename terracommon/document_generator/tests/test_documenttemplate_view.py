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
        fake_userrequest = UserRequestFactory(properties={
            'from': '01/01/2018',
            'to': '31/12/2018',
            'registration': 'AS-AS-AA-AS-AS',
            'authorization': 'okay'
        })

        # Mock?
        DocumentGenerator.get_pdf = Mock(return_value=b'this is a PDF-1.4\n'
                                                      b'Well I think it is.')

        # Calling the Api with good params
        response = self.client.post(reverse('document-pdf',
                                            kwargs={
                                             'request_pk': fake_userrequest.pk,
                                             'pk': myodt.pk
                                            }))

        # Assertion
        self.assertEqual(200, response.status_code)

        DocumentGenerator.get_pdf.assert_called_with(
            fake_userrequest.properties)

        pdf_header = response.content.split(b'\n')[0]
        self.assertIn(b'PDF', pdf_header)

        # Testing bad request_pk
        response_404 = self.client.post(reverse('document-pdf',
                                                kwargs={
                                                    'request_pk': 9999,
                                                    'pk': myodt.pk
                                                }))
        self.assertEqual(404, response_404.status_code)

        # Testing bad pk
        userreq_pk = fake_userrequest.pk  # for linting purpose
        response_404 = self.client.post(reverse('document-pdf',
                                                kwargs={
                                                    'request_pk': userreq_pk,
                                                    'pk': 9999
                                                }))
        self.assertEqual(404, response_404.status_code)
