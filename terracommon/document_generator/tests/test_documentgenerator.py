import io
import os
from unittest.mock import MagicMock, patch
from uuid import uuid4

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from jinja2 import TemplateSyntaxError

from terracommon.accounts.tests.factories import TerraUserFactory
from terracommon.document_generator.helpers import DocumentGenerator
from terracommon.document_generator.models import (DocumentTemplate,
                                                   DownloadableDocument)
from terracommon.trrequests.tests.factories import UserRequestFactory


def mock_libreoffice(arguments):
    tmp_pdf_root = os.path.splitext(os.path.basename(arguments[-1]))[0]
    tmp_pdf = os.path.join('/tmp', f'{tmp_pdf_root}.pdf')
    with open(tmp_pdf, 'wb') as pdf_file:
        pdf_file.write(b'some content')


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

    @patch('subprocess.run', side_effect=mock_libreoffice)
    def test_pdf_is_generated_from_enriched_docx(self, mock_run):
        # Patch libroffice call, that should write a pdf file of the same name
        # as temporary docx file

        # Now patch get_docx to return dumb content
        docx_path = os.path.join(os.path.dirname(__file__), 'empty.docx')
        with open(docx_path, 'rb') as docx_file:
            with patch.object(
                    DocumentGenerator, 'get_docx',
                    return_value=io.BytesIO(docx_file.read())
            ) as mock_docx:
                dg = DocumentGenerator(self.downloadable)
                pdf_path = dg.get_pdf()
                mock_docx.assert_called()
                os.remove(pdf_path)

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

    @patch('subprocess.run', side_effect=mock_libreoffice)
    def test_cache_is_created(self, mock_run):
        dg = DocumentGenerator(self.downloadable)
        pdf_path = dg.get_pdf()

        self.assertTrue(os.path.isfile(pdf_path))
        os.remove(pdf_path)

    @patch('terracommon.document_generator.helpers.logger')
    def test_raises_templatesyntaxerror_exception(self, mock_logger):
        dg = DocumentGenerator(self.downloadable)
        dg.get_docx = MagicMock(side_effect=TemplateSyntaxError('', 0))

        with self.assertRaises(TemplateSyntaxError):
            dg.get_pdf()
            mock_logger.warning.assert_called()

    @patch('subprocess.run', side_effect=mock_libreoffice)
    def test_pdf_is_generated_again_when_data_are_updated(self, mock_run):
        dg = DocumentGenerator(self.downloadable)
        pdf_path = dg.get_pdf()
        pdf_mtime = os.path.getmtime(pdf_path)

        self.assertTrue(os.path.isfile(pdf_path))

        self.userrequest.properties = {'test_key': 'test_value'}
        self.userrequest.save()

        dg_bis = DocumentGenerator(self.downloadable)
        pdf_path_bis = dg_bis.get_pdf()
        self.assertTrue(os.path.isfile(pdf_path_bis))
        self.assertNotEqual(os.path.getmtime(pdf_path_bis), pdf_mtime)
