import os

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.test.client import RequestFactory
from rest_framework import status

from terracommon.document_generator.helpers import get_media_response


class MediaResponseTest(TestCase):
    def setUp(self):
        self.factory = RequestFactory()

    def test_get_media_response_with_path(self):
        request = self.factory.get('fake/path')

        # Creating a real file
        # In this case, we test if get_media_response return content
        # from a file and so will use open()
        tmp_name = '/tmp/test.txt'
        with open(tmp_name, 'wb') as tmp_file:
            tmp_file.write(b"ceci n'est pas une pipe")

        response = get_media_response(
            request,
            {'path': tmp_name, 'url': None}  # url none, no accel-redirect
        )

        # deleting the file since we don't need it anymore
        os.remove(tmp_name)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsInstance(response.content, bytes)
        self.assertEqual(response.content, b"ceci n'est pas une pipe")

    def test_get_media_response_with_file_object(self):
        request = self.factory.get('fake/path')

        tmp_file = SimpleUploadedFile(name='/tmp/file.txt',
                                      content=b'creativity takes courage')

        # Adding fake url, we don't care, we are not testing accel-redirect
        tmp_file.url = None

        response = get_media_response(request, tmp_file)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsInstance(response.content, bytes)
        self.assertEqual(response.content, b'creativity takes courage')
