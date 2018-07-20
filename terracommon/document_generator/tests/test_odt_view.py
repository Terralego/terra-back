import os
from unittest.mock import Mock

from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient

from terracommon.accounts.tests.factories import TerraUserFactory
from terracommon.document_generator.helpers import DocumentGenerator
from terracommon.document_generator.models import OdtFile
from terracommon.trrequests.tests.factories import UserRequestFactory


class OdtViewTestCase(TestCase):
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
        myodt = OdtFile(name='testodt', odt=tmp_odt)
        myodt.save()

        # Create a fake UserRequest
        fake_userrequest = UserRequestFactory()
        fake_userrequest.properties = {
            'from': '01/01/2018',
            'to': '31/12/2018',
            'registration': 'AS-AS-AA-AS-AS',
            'authorization': 'okay'
        }
        fake_userrequest.save()

        # Mock?
        DocumentGenerator.get_pdf = Mock(return_value=b'this is a PDF-1.4\n'
                                                      b'Well I think it is.')

        # Calling the Api with good params
        response = self.client.post(reverse('odtfile-pdf-creator',
                                            kwargs={
                                             'userreq_id': fake_userrequest.pk,
                                             'pk': myodt.pk
                                            }))

        # Assertion
        self.assertEqual(200, response.status_code)

        DocumentGenerator.get_pdf.assert_called_with(
            fake_userrequest.properties)

        pdf_header = response.content.split(b'\n')[0]
        self.assertIs(True, b'PDF' in pdf_header)
