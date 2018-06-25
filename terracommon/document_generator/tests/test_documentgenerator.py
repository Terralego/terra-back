import os
from unittest.mock import MagicMock

import requests
from django.conf import settings
from django.test import TestCase
from requests import HTTPError, Response

from terracommon.document_generator.helpers import DocumentGenerator


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
