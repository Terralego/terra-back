import os
from datetime import date
from tempfile import NamedTemporaryFile
from unittest.mock import patch

from django.conf import settings
from django.contrib.auth.tokens import default_token_generator
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
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
        tmp_docx = os.path.join('terracommon',
                                'document_generator',
                                'tests',
                                'test_template.docx')

        # Store it in the database
        DocumentTemplate.objects.create(name='testdocx',
                                        documenttemplate=tmp_docx)
        self.docx = DocumentTemplate.objects.get(name='testdocx')

        # Create a fake UserRequest
        self.properties = {
            'from': '01/01/2018',
            'to': '31/12/2018',
            'registration': 'AS-AS-AA-AS-AS',
            'authorization': 'okay'
        }
        self.pdfcreator_urlname = 'document_generator:document-pdf'

    def test_pdf_creator_method_with_dev_settings(self):
        fake_userrequest = UserRequestFactory(properties=self.properties)
        pks = {'request_pk': fake_userrequest.pk, 'pk': self.docx.pk}

        # Create permissions
        DownloadableDocument.objects.create(
            user=self.user,
            document=self.docx,
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
            uidb64, token = self.get_uidb64_token_for_user()
            document_url = reverse(self.pdfcreator_urlname,
                                   kwargs=pks)
            # Testing with no MEDIA_ACCEL_REDIRECT
            response = self.client.get(
                f'{document_url}?token={token}&uidb64={uidb64}')
            self.assertEqual(status.HTTP_200_OK, response.status_code)
            self.assertEqual('application/pdf', response['Content-Type'])
            self.assertEqual(f'attachment;filename={pdf_name}',
                             response['Content-Disposition'])

            self.assertEqual(response.content, fake_pdf.read())

            mock_dg.assert_called_with()

        os.remove(fake_pdf.name)

    def test_pdf_creator_method_with_prod_settings(self):
        userrequest = UserRequestFactory(properties=self.properties)
        pks = {'request_pk': userrequest.pk, 'pk': self.docx.pk}

        # Create permissions
        DownloadableDocument.objects.create(
            user=self.user,
            document=self.docx,
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
                uidb64, token = self.get_uidb64_token_for_user()
                pdf_url = reverse(self.pdfcreator_urlname,
                                  kwargs=pks)
                response = self.client.get(
                    f'{pdf_url}?token={token}&uidb64={uidb64}')

                self.assertEqual(status.HTTP_200_OK, response.status_code)
                self.assertEqual('application/pdf', response['Content-Type'])
                self.assertEqual(f'attachment;filename={pdf_name}',
                                 response['Content-Disposition'])
                self.assertIn(settings.MEDIA_URL,
                              response.get('X-Accel-Redirect'))
                mock_dg.assert_called_with()

        os.remove(fake_pdf.name)

    def test_pdf_creator_with_bad_requestpk(self):
        # Testing bad request_pk
        pks = {'request_pk': 999, 'pk': self.docx.pk}
        uidb64, token = self.get_uidb64_token_for_user()
        pdf_url = reverse(self.pdfcreator_urlname,
                          kwargs=pks)
        response = self.client.get(
            f'{pdf_url}?token={token}&uidb64={uidb64}')

        self.assertEqual(status.HTTP_404_NOT_FOUND, response.status_code)

    def test_pdf_creator_with_bad_pk(self):
        fake_userrequest = UserRequestFactory(properties=self.properties)
        DownloadableDocument.objects.create(
            user=self.user,
            document=self.docx,
            linked_object=fake_userrequest
        )
        # Testing bad pk
        pks = {'request_pk': fake_userrequest.pk, 'pk': 9999}
        uidb64, token = self.get_uidb64_token_for_user()
        pdf_url = reverse(self.pdfcreator_urlname,
                          kwargs=pks)
        response = self.client.get(
            f'{pdf_url}?token={token}&uidb64={uidb64}')
        self.assertEqual(status.HTTP_404_NOT_FOUND, response.status_code)

    def test_pdf_creator_without_download_pdf_permissions(self):
        userrequest = UserRequestFactory(properties=self.properties)
        pks = {'request_pk': userrequest.pk, 'pk': self.docx.pk}
        uidb64, token = self.get_uidb64_token_for_user()
        pdf_url = reverse(self.pdfcreator_urlname,
                          kwargs=pks)
        response = self.client.get(
            f'{pdf_url}?token={token}&uidb64={uidb64}')
        response = self.client.get(response)

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

            # Create another user to verify if the permission
            # Allow to Download document from other user request
            user = TerraUserFactory()
            DownloadableDocument.objects.create(
                user=user,
                document=self.docx,
                linked_object=userrequest
            )
            pks = {'request_pk': userrequest.pk, 'pk': self.docx.pk}
            uidb64, token = self.get_uidb64_token_for_user()
            pdf_url = reverse(self.pdfcreator_urlname,
                              kwargs=pks)
            response = self.client.get(
                f'{pdf_url}?token={token}&uidb64={uidb64}')

            self.assertEqual(status.HTTP_200_OK, response.status_code)

            self.client.force_authenticate(user=None)
            response = self.client.get(
                f'{pdf_url}?token={token}&uidb64={uidb64}')

            self.assertEqual(status.HTTP_200_OK, response.status_code)

            mock_dg.assert_called()

        os.remove(fake_pdf.name)

    def test_pdf_creator_with_authentication(self):
        fake_userrequest = UserRequestFactory(properties=self.properties)

        # Testing unauthenticated user
        self.client.force_authenticate(user=None)
        pks = {'request_pk': fake_userrequest.pk, 'pk': self.docx.pk}
        uidb64, token = self.get_uidb64_token_for_user()
        pdf_url = reverse(self.pdfcreator_urlname,
                          kwargs=pks)
        response = self.client.get(
            f'{pdf_url}?token={token}&uidb64={uidb64}')
        self.assertEqual(status.HTTP_404_NOT_FOUND, response.status_code)

        # Reseting default test settings
        self.client.force_authenticate(user=self.user)

    def test_raises_filenotfounderror_return_404(self):
        ur = UserRequestFactory()
        pks = {'request_pk': ur.pk, 'pk': self.docx.pk}

        # Creating Permission
        DownloadableDocument.objects.create(user=self.user,
                                            document=self.docx,
                                            linked_object=ur)
        # Mocking getpdf
        with patch.object(DocumentGenerator,
                          'get_pdf',
                          side_effect=FileNotFoundError) as mock_dg:
            uidb64, token = self.get_uidb64_token_for_user()
            pdf_url = reverse(self.pdfcreator_urlname,
                              kwargs=pks)
            response = self.client.get(
                f'{pdf_url}?token={token}&uidb64={uidb64}')
            self.assertEqual(status.HTTP_404_NOT_FOUND, response.status_code)
            mock_dg.assert_called_with()

    def test_raises_HTTPError_return_503(self):
        ur = UserRequestFactory()
        pks = {'request_pk': ur.pk, 'pk': self.docx.pk}

        # Creating Permission
        DownloadableDocument.objects.create(user=self.user,
                                            document=self.docx,
                                            linked_object=ur)
        # Mocking getpdf
        with patch.object(DocumentGenerator,
                          'get_pdf',
                          side_effect=HTTPError) as mock_dg:
            uidb64, token = self.get_uidb64_token_for_user()
            pdf_url = reverse(self.pdfcreator_urlname,
                              kwargs=pks)
            response = self.client.get(
                f'{pdf_url}?token={token}&uidb64={uidb64}')
            self.assertEqual(status.HTTP_503_SERVICE_UNAVAILABLE,
                             response.status_code)
            mock_dg.assert_called_with()

    def test_raises_ConnectionError_return_503(self):
        ur = UserRequestFactory()
        pks = {'request_pk': ur.pk, 'pk': self.docx.pk}

        # Creating Permission
        DownloadableDocument.objects.create(user=self.user,
                                            document=self.docx,
                                            linked_object=ur)
        # Mocking getpdf
        with patch.object(DocumentGenerator,
                          'get_pdf',
                          side_effect=ConnectionError) as mock_dg:
            uidb64, token = self.get_uidb64_token_for_user()
            pdf_url = reverse(self.pdfcreator_urlname,
                              kwargs=pks)
            response = self.client.get(
                f'{pdf_url}?token={token}&uidb64={uidb64}')
            self.assertEqual(status.HTTP_503_SERVICE_UNAVAILABLE,
                             response.status_code)
            mock_dg.assert_called_with()

    def test_raises_TemplateSyntaxError_return_500(self):
        ur = UserRequestFactory()
        pks = {'request_pk': ur.pk, 'pk': self.docx.pk}

        # Creating Permission
        DownloadableDocument.objects.create(user=self.user,
                                            document=self.docx,
                                            linked_object=ur)
        # Mocking getpdf
        with patch.object(
                DocumentGenerator,
                'get_pdf',
                side_effect=TemplateSyntaxError(message='error',
                                                lineno=1)) as mock_dg:
            uidb64, token = self.get_uidb64_token_for_user()
            pdf_url = reverse(self.pdfcreator_urlname,
                              kwargs=pks)
            response = self.client.get(
                f'{pdf_url}?token={token}&uidb64={uidb64}')
            self.assertEqual(status.HTTP_500_INTERNAL_SERVER_ERROR,
                             response.status_code)
            mock_dg.assert_called_with()

    def test_create_document_template_with_permission(self):
        file_tpl = SimpleUploadedFile(
            'a/super/path',
            b'me like pizza',
            content_type='multipart/form-data'
        )
        self._set_permissions(['can_upload_template', ])

        response = self.client.post(
            reverse('document_generator:document-list'),
            {
                'name': file_tpl.name,
                'documenttemplate': file_tpl,
                'uid': 'test_uid'
            },
            format='multipart'
        )
        self.assertEqual(status.HTTP_201_CREATED, response.status_code)
        self.assertTrue(
            DocumentTemplate.objects.filter(name=file_tpl.name,
                                            uid='test_uid').exists()
        )

    def test_create_false_document_template_with_permission(self):
        file_tpl = SimpleUploadedFile(
            '',
            b'me like pizza',
            content_type='multipart/form-data'
        )
        self._set_permissions(['can_upload_template', ])

        response = self.client.post(
            reverse('document_generator:document-list'),
            {
                'name': file_tpl.name,
                'documenttemplate': file_tpl,
                'uid': 'test_uid'
            },
            format='multipart'
        )
        self.assertEqual(status.HTTP_400_BAD_REQUEST, response.status_code)
        self.assertFalse(
            DocumentTemplate.objects.filter(name=file_tpl.name,
                                            uid='test_uid').exists()
        )

    def test_create_document_template_without_permission(self):
        response = self.client.post(
            reverse('document_generator:document-list'),
            {
                'name': 'refused_doc',
                'documenttemplate': SimpleUploadedFile(
                    'path/to/doc',
                    b'refused content',
                    content_type='multipart/form-data'
                ),
                'uid': 'refused document'
            },
            format='multipart'
        )
        self.assertEqual(status.HTTP_403_FORBIDDEN, response.status_code)
        self.assertFalse(
            DocumentTemplate.objects.filter(name='refuse_doc',
                                            uid='refused document').exists()
        )

    def test_update_document_template_with_permissions(self):
        # File send for patch
        txt_tpl = b'me like pizza'
        file_tpl = SimpleUploadedFile(
            'a/another/path',
            txt_tpl,
            content_type='multipart/form-data'
        )

        # File updated in database
        doc_tpl = DocumentTemplate.objects.create(
            name="martine",
            documenttemplate=SimpleUploadedFile(
                'a/new/path',
                b'martine likes pizza',
            ),
            uid="new_uid"
        )

        self._set_permissions(['can_update_template', ])

        response = self.client.patch(
            reverse('document_generator:document-detail',
                    kwargs={"pk": doc_tpl.pk}),
            {
                'name': file_tpl.name,
                'documenttemplate': file_tpl,
                'uid': 'test_uid'
            },
            format='multipart'
        )

        self.assertEqual(status.HTTP_200_OK, response.status_code)

        doc_tpl_updated = DocumentTemplate.objects.get(pk=doc_tpl.pk)

        self.assertEqual(file_tpl.name, doc_tpl_updated.name)
        self.assertEqual("test_uid", doc_tpl_updated.uid)

        with open(doc_tpl_updated.documenttemplate.path, "rb") as dtu:
            self.assertEqual(txt_tpl, dtu.read())

    def test_bad_update_document_template_with_permission(self):
        tpl_text = b'martine likes pizza'
        # File to update in database
        doc_tpl = DocumentTemplate.objects.create(
            name="martine",
            documenttemplate=SimpleUploadedFile(
                'a/new/path',
                tpl_text,
            ),
            uid="new_uid"
        )

        # File send for patch
        file_tpl = SimpleUploadedFile(
            '',
            b'me likes pineapple pen',
            content_type='multipart/form-data'
        )

        self._set_permissions(['can_update_template', ])
        response = self.client.patch(
            reverse('document_generator:document-detail',
                    kwargs={'pk': doc_tpl.pk}),
            {
                'name': file_tpl.name,
                'documenttemplate': file_tpl,
                'uid': 'wrong_uid'
            },
            format='multipart',
        )

        self.assertEqual(status.HTTP_400_BAD_REQUEST, response.status_code)

        doc_tpl_not_updated = DocumentTemplate.objects.get(pk=doc_tpl.pk)
        self.assertEqual(doc_tpl.name, doc_tpl_not_updated.name)
        self.assertEqual(doc_tpl.uid, doc_tpl_not_updated.uid)

        with open(doc_tpl_not_updated.documenttemplate.path, 'rb') as dtnu:
            self.assertEqual(tpl_text, dtnu.read())

    def test_update_document_template_without_permission(self):
        # Document in the base to update
        txt_tpl = b'no content'
        doc_tpl = DocumentTemplate.objects.create(
            name='initial.doc',
            documenttemplate=SimpleUploadedFile('path/to/doc', txt_tpl),
            uid='initial document'
        )
        response = self.client.patch(
            reverse('request-detail', kwargs={'pk': doc_tpl.pk}),
            {
                'name': 'refused.doc',
                'documenttemplate': SimpleUploadedFile(
                    'path/to/refuseddoc',
                    b'refused content',
                    content_type='multipart/form-data'
                ),
                'uid': 'refused document'
            },
            format='multipart'
        )

        self.assertEqual(status.HTTP_404_NOT_FOUND, response.status_code)

        not_updated_doc_tpl = DocumentTemplate.objects.get(pk=doc_tpl.pk)
        self.assertEqual(not_updated_doc_tpl.name, doc_tpl.name)
        self.assertEqual(not_updated_doc_tpl.uid, doc_tpl.uid)
        with open(not_updated_doc_tpl.documenttemplate.path, 'rb') as dt:
            self.assertEqual(txt_tpl, dt.read())

    def test_delete_document_template_with_permission(self):
        # File to delete in the database
        doc_tpl = DocumentTemplate.objects.create(
            name='michel',
            documenttemplate=SimpleUploadedFile('a/fake/path', b'no content'),
            uid='file to delete'
        )

        self._set_permissions(['can_delete_template', ])
        response = self.client.delete(
            reverse(
                'document_generator:document-detail',
                kwargs={'pk': doc_tpl.pk}
            )
        )

        self.assertEqual(status.HTTP_204_NO_CONTENT, response.status_code)
        self.assertFalse(
            DocumentTemplate.objects.filter(name='michel',
                                            uid='file to delete').exists()
        )

    def test_delete_document_template_with_permission_bad_pk(self):
        # File to delete in the database
        DocumentTemplate.objects.create(
            name='michel',
            documenttemplate=SimpleUploadedFile('a/fake/path', b'no content'),
            uid='file to delete'
        )

        self._set_permissions(['can_delete_template', ])
        response = self.client.delete(
            reverse(
                'document_generator:document-detail',
                kwargs={'pk': '666'}
            )
        )

        self.assertEqual(status.HTTP_404_NOT_FOUND, response.status_code)
        self.assertTrue(
            DocumentTemplate.objects.filter(name='michel',
                                            uid='file to delete').exists()
        )

    def test_delete_document_template_without_permissions(self):
        doc_tpl = DocumentTemplate.objects.create(
            name='doc_to_delete',
            documenttemplate=SimpleUploadedFile('path/to.doc', b'no content'),
            uid='document to delete',
        )
        response = self.client.delete(reverse(
            'document_generator:document-detail',
            kwargs={'pk': doc_tpl.pk})
        )
        self.assertEqual(status.HTTP_403_FORBIDDEN, response.status_code)
        self.assertTrue(
            DocumentTemplate.objects.filter(pk=doc_tpl.pk).exists()
        )

    def get_uidb64_token_for_user(self):
        return (urlsafe_base64_encode(force_bytes(self.user.pk)).decode(),
                default_token_generator.make_token(self.user))
