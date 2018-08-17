import os
from unittest.mock import Mock

from django.core.files.uploadedfile import SimpleUploadedFile
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
        tmp_odt = os.path.join(*['terracommon', 'document_generator', 'tests'],
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
        cache_filename = (f'cache/{self.myodt.documenttemplate}'
                          f'{self.myodt.name}_'
                          f'{fake_userrequest.__class__.__name__}_'
                          f'{fake_userrequest.pk}.pdf')

        # Mocking
        fake_pdf = SimpleUploadedFile('mypdf.pdf',
                                      b'Header PDF-1.4\nsome line.')
        DocumentGenerator.get_pdf = Mock(return_value=fake_pdf)

        # Testing with no MEDIA_ACCEL_REDIRECT
        response = self.client.post(reverse(self.pdfcreator_urlname,
                                            kwargs=pks))
        self.assertEqual(status.HTTP_200_OK, response.status_code)
        self.assertEqual('application/pdf', response['Content-Type'])
        self.assertEqual(f'attachment;filename={cache_filename}',
                         response['Content-Disposition'])

        self.assertTrue(os.path.isfile(cache_filename))

        fake_pdf.seek(0)
        self.assertEqual(response.content, fake_pdf.read())

        DocumentGenerator.get_pdf.assert_called_with(
            fake_userrequest.properties
        )

        os.remove(cache_filename)
        self.assertFalse(os.path.isfile(cache_filename))

    def test_pdf_creator_method_with_prod_settings(self):
        userrequest = UserRequestFactory(properties=self.properties)
        pks = {'request_pk': userrequest.pk, 'pk': self.myodt.pk}

        # Create permissions
        DownloadableDocument.objects.create(
            user=self.user,
            document=self.myodt,
            linked_object=userrequest
        )
        cache_filename = (f'cache/{self.myodt.documenttemplate}'
                          f'{self.myodt.name}_'
                          f'{userrequest.__class__.__name__}_'
                          f'{userrequest.pk}.pdf')

        fake_pdf = SimpleUploadedFile('mypdf.pdf',
                                      b'Header PDF-1.4\nsome line.')
        DocumentGenerator.get_pdf = Mock(return_value=fake_pdf)

        with self.settings(MEDIA_ACCEL_REDIRECT=True):
            response = self.client.post(reverse(self.pdfcreator_urlname,
                                                kwargs=pks))
        self.assertEqual(status.HTTP_200_OK, response.status_code)
        self.assertEqual('application/pdf', response['Content-Type'])
        self.assertEqual(f'attachment;filename={cache_filename}',
                         response['Content-Disposition'])

        DocumentGenerator.get_pdf.assert_called_with(
            userrequest.properties
        )
        self.assertTrue(os.path.isfile(cache_filename))

        cached_doc = CachedDocument(open(cache_filename))
        self.assertEqual(response.get('X-Accel-Redirect'),
                         cached_doc.url)
        cached_doc.close()
        cached_doc.remove()
        self.assertFalse(os.path.isfile(cache_filename))

    def test_pdf_creator_method_with_existing_cache(self):
        userrequest = UserRequestFactory(properties=self.properties)
        pks = {'request_pk': userrequest.pk, 'pk': self.myodt.pk}

        # Creating user permission
        DownloadableDocument.objects.create(
            user=self.user,
            document=self.myodt,
            linked_object=userrequest
        )

        # Mocking get_pdf method using convertit
        DocumentGenerator.get_pdf = Mock()

        # Creating a `cache file`
        cache_filename = (f'cache/{self.myodt.documenttemplate}'
                          f'{self.myodt.name}_'
                          f'{userrequest.__class__.__name__}_'
                          f'{userrequest.pk}.pdf')

        # Create subdirs if need some and they do not exist yet.
        os.makedirs(os.path.dirname(cache_filename), exist_ok=True)
        fake_cache = CachedDocument(open(cache_filename, 'wb'))
        fake_cache.write(b'Header PDF-1.4\nSome line.\n')
        fake_cache.close()

        # Calling API and asserting Response
        response = self.client.post(reverse(self.pdfcreator_urlname,
                                            kwargs=pks))
        self.assertEqual(status.HTTP_200_OK, response.status_code)

        # Asserting DocumentGenerator.get_pdf was not call
        # Because cache already existed
        DocumentGenerator.get_pdf.assert_not_called()

        # Checking and clearing Cache
        self.assertTrue(os.path.isfile(cache_filename))

        fake_cache.remove()
        self.assertFalse(os.path.isfile(cache_filename))

    def test_pdf_creator_with_bad_requestpk(self):
        # Testing bad request_pk
        pks = {'request_pk': 999, 'pk': self.myodt.pk}

        response = self.client.post(reverse(self.pdfcreator_urlname,
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

        response = self.client.post(reverse(self.pdfcreator_urlname,
                                            kwargs=pks))
        self.assertEqual(status.HTTP_404_NOT_FOUND, response.status_code)

    def test_pdf_creator_without_download_pdf_permissions(self):
        userrequest = UserRequestFactory(properties=self.properties)
        pks = {'request_pk': userrequest.pk, 'pk': self.myodt.pk}

        response = self.client.post(reverse(self.pdfcreator_urlname,
                                            kwargs=pks))

        self.assertEqual(status.HTTP_403_FORBIDDEN, response.status_code)

    def test_pdf_creator_with_all_pdf_permission(self):
        self._set_permissions(['can_download_all_pdf', ])

        fake_pdf = SimpleUploadedFile('mypdf.pdf',
                                      b'Header PDF-1.4\nsome line.')
        DocumentGenerator.get_pdf = Mock(return_value=fake_pdf)

        userrequest = UserRequestFactory(properties=self.properties)
        pks = {'request_pk': userrequest.pk, 'pk': self.myodt.pk}

        response = self.client.post(reverse(self.pdfcreator_urlname,
                                            kwargs=pks))

        self.assertEqual(status.HTTP_200_OK, response.status_code)

        # Checking and Clearing Cache
        cache_filename = (f'cache/{self.myodt.documenttemplate}'
                          f'{self.myodt.name}_'
                          f'{userrequest.__class__.__name__}_'
                          f'{userrequest.pk}.pdf')
        self.assertTrue(os.path.isfile(cache_filename))

        os.remove(cache_filename)
        self.assertFalse(os.path.isfile(cache_filename))

    def test_pdf_creator_with_authentication(self):
        fake_userrequest = UserRequestFactory(properties=self.properties)

        # Testing unauthenticated user
        self.client.force_authenticate(user=None)
        pks = {'request_pk': fake_userrequest.pk, 'pk': self.myodt.pk}

        response = self.client.post(reverse(self.pdfcreator_urlname,
                                            kwargs=pks))
        self.assertEqual(status.HTTP_401_UNAUTHORIZED, response.status_code)
