import io
import os
from tempfile import NamedTemporaryFile
from unittest.mock import MagicMock, PropertyMock, patch
from uuid import uuid4

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from jinja2 import TemplateSyntaxError

from terracommon.accounts.tests.factories import TerraUserFactory
from terracommon.document_generator.helpers import DocumentGenerator
from terracommon.document_generator.models import (DocumentTemplate,
                                                   DownloadableDocument)
from terracommon.trrequests.tests.factories import UserRequestFactory


class DocumentGeneratorTestCase(TestCase):
    def setUp(self):
        self.user = TerraUserFactory()
        self.userrequest = UserRequestFactory()
        self.docx_file = os.path.join(os.path.dirname(__file__), 'empty.docx')
        with open(self.docx_file, 'rb') as docx:
            self.template = DocumentTemplate.objects.create(
                name='emptydocx',
                documenttemplate=SimpleUploadedFile(
                    str(uuid4()),
                    docx.read()
                )
            )
        self.downloadable = DownloadableDocument.objects.create(
            user=self.user,
            document=self.template,
            linked_object=self.userrequest
        )

    def test_pdf_is_generated_from_enriched_docx(self):
        pdf_file = NamedTemporaryFile(
            mode='wb',
            delete=False,
            prefix='/tmp/',
            suffix='.pdf',
        )

        with patch('subprocess.call',
                   new_callable=PropertyMock) as mock_content:
            mock_content.side_effect = pdf_file.write(b'some content')

            docx_path = os.path.join(os.path.dirname(__file__), 'empty.docx')
            docx_file = open(docx_path, 'rb')

            dg = DocumentGenerator(self.downloadable)
            dg.get_docx = MagicMock(return_value=io.BytesIO(docx_file.read()))
            pdf_path = dg.get_pdf()
            dg.get_docx.assert_called()

            os.remove(pdf_path)
        os.remove(pdf_file.name)

    def test_everything_seems_to_work_without_variables(self):
        dg = DocumentGenerator(self.downloadable)
        dg.get_docx({})  # No exceptions are raised

    def test_everything_seems_to_work_with_variables(self):
        template_path = os.path.join(os.path.dirname(__file__),
                                     'template_with_img.docx')

        with open(template_path, 'rb') as template_fd:
            template = DocumentTemplate.objects.create(
                name='template_with_img',
                documenttemplate=SimpleUploadedFile(template_path,
                                                    template_fd.read())
            )
        downloadable = DownloadableDocument.objects.create(
            user=self.user,
            document=template,
            linked_object=self.userrequest
        )
        image_path = os.path.join(os.path.dirname(__file__), 'new_img.png')
        dg = DocumentGenerator(downloadable)
        dg.get_docx({
            'name': 'Makina Corpus',
            'logo': image_path,
        })  # No exceptions are raised

    def test_raises_exception_typeerror(self):
        with self.assertRaises(TypeError):
            DocumentGenerator('')

    @patch('terracommon.document_generator.helpers.logger')
    def test_raises_exception_when_template_is_not_found(self, mock_logger):
        dg = DocumentGenerator(self.downloadable)
        dg.get_docx = MagicMock(side_effect=FileNotFoundError)
        with self.assertRaises(FileNotFoundError):
            dg.get_pdf()
            mock_logger.warning.assert_called()

    def test_cache_is_created(self):
        pdf_file = NamedTemporaryFile(
            mode='wb',
            delete=False,
            prefix='/tmp/',
            suffix='.pdf'
        )

        with patch('subprocess.call',
                   new_callable=PropertyMock) as mock_content:
            mock_content.side_effect = pdf_file.write(b'some content')
            pdf_file.close()

            with open(self.docx_file, 'rb') as docx_file:
                dg = DocumentGenerator(self.downloadable)
                dg.get_docx = MagicMock(
                    return_value=io.BytesIO(docx_file.read())
                )
                pdf_path = dg.get_pdf()

                self.assertTrue(os.path.isfile(pdf_path))
                os.remove(pdf_path)
            os.remove(pdf_file.name)

    @patch('terracommon.document_generator.helpers.logger')
    def test_raises_templatesyntaxerror_exception(self, mock_logger):
        dg = DocumentGenerator(self.downloadable)
        dg.get_docx = MagicMock(side_effect=TemplateSyntaxError('', 0))

        with self.assertRaises(TemplateSyntaxError):
            dg.get_pdf()
            mock_logger.warning.assert_called()
