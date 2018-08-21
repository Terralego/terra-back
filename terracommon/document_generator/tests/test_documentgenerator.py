import os
from unittest.mock import MagicMock, PropertyMock, patch

import requests
from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from requests import HTTPError, Response

from terracommon.document_generator.helpers import (CachedDocument,
                                                    DocumentGenerator)
from terracommon.trrequests.tests.factories import UserRequestFactory


class DocumentGeneratorTestCase(TestCase):
    def test_pdf_is_generated_from_enriched_odt(self):
        convertit_response = Response()
        convertit_response.url = settings.CONVERTIT_URL
        convertit_response.status_code = 200
        requests.post = MagicMock(return_value=convertit_response)

        odt_path = os.path.join(os.path.dirname(__file__), 'empty.odt')
        odt_file = open(odt_path, 'rb')

        dg = DocumentGenerator(odt_file)
        dg.get_odt = MagicMock(return_value=odt_file)
        dg.get_pdf({})
        dg.get_odt.assert_called()

    def test_everything_seems_to_work_without_variables(self):
        template_path = os.path.join(os.path.dirname(__file__), 'empty.odt')
        dg = DocumentGenerator(template_path)
        dg.get_odt({})  # No exceptions are raised

    def test_everything_seems_to_work_with_variables(self):
        template_path = os.path.join(os.path.dirname(__file__),
                                     'template_with_img.odt')
        image_path = os.path.join(os.path.dirname(__file__), 'new_img.png')
        dg = DocumentGenerator(template_path)
        dg.get_odt({
            'name': 'Makina Corpus',
            'logo': image_path,
        })  # No exceptions are raised

    def test_raises_exception_when_template_is_not_found(self):
        dg = DocumentGenerator('')
        with self.assertRaises(FileNotFoundError):
            dg.get_pdf({})

    def test_raises_exception_when_convertit_does_not_answer(self):
        mock_response = Response()
        mock_response.url = settings.CONVERTIT_URL
        mock_response.status_code = 404
        requests.post = MagicMock(return_value=mock_response)

        template = os.path.join(os.path.dirname(__file__),
                                'empty.odt')
        dg = DocumentGenerator(template)
        with self.assertRaises(HTTPError):
            dg.get_pdf({})

    def test_cache_is_created(self):
        fake_pdf = SimpleUploadedFile('fake.pdf', b'file content')
        fake_pdf.seek(0)

        with patch('requests.Response.content',
                   new_callable=PropertyMock) as mock_content:
            mock_content.return_value = fake_pdf
            response_convertit = Response()
            response_convertit.url = settings.CONVERTIT_URL
            response_convertit.status_code = 200
            requests.post = MagicMock(return_value=response_convertit)

            odt_path = os.path.join(os.path.dirname(__file__), 'empty.odt')
            odt_file = open(odt_path, 'rb')

            userrequest = UserRequestFactory(properties={'a': 'a'})

            dg = DocumentGenerator(odt_file)
            dg.get_odt = MagicMock(return_value=odt_file)
            fake_pdf = dg.get_pdf(userrequest)

            self.assertTrue(isinstance(fake_pdf, CachedDocument))
            self.assertTrue(os.path.isfile(fake_pdf.name))

            fake_pdf.remove()
            self.assertFalse(os.path.isfile(fake_pdf.name))
