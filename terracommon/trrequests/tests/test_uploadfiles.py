from io import StringIO

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from terracommon.trrequests.models import UploadFile

from .factories import CommentFactory
from .mixins import TestPermissionsMixin


class UploadFilesTestCase(TestCase, TestPermissionsMixin):

    def setUp(self):
        self.client = APIClient()

        self.comment = CommentFactory()
        self.request = self.comment.userrequest
        self.user = self.comment.owner
        self.client.force_authenticate(user=self.user)

    def test_creation(self):
        tmp_file = StringIO('Lorem ipsum')
        tmp_file.name = 'first.txt'
        creation_data = {
            'name': 'Filename',
            'file': tmp_file,
        }

        creation_response = self.client.post(
            reverse('file-list', args=[self.request.pk, self.comment.pk, ]),
            creation_data,
            'multipart'
        )
        self.assertEqual(status.HTTP_201_CREATED,
                         creation_response.status_code)

        creation_response = creation_response.json()
        self.assertTrue(UploadFile.objects.get(pk=creation_response.get('id')))
        uf = UploadFile.objects.get(pk=creation_response.get('id'))
        self.assertEqual(creation_data['name'], uf.name)
        self.assertNotIn(tmp_file.name, uf.file.name)

    def test_list(self):
        uf = self.comment.files.create(
            comment=self.comment,
            name='My file',
            initial_filename='second.txt',
            file=SimpleUploadedFile('second.txt', b'Foo bar')
        )
        self.assertNotIn('second.txt', uf.file.name)

        list_response = self.client.get(
            reverse('file-list', args=[self.request.pk, self.comment.pk, ]))
        self.assertEqual(status.HTTP_200_OK, list_response.status_code)
        list_response = list_response.json()
        results = list(filter(lambda r: r.get('id', 0) == uf.pk,
                              list_response.get('results', [])))
        self.assertEqual(1, len(results))
        result = results[0]
        self.assertEqual(uf.name, result.get('name'))
        self.assertIn(reverse('file-download',
                              args=[self.request.pk, self.comment.pk, uf.pk]),
                      result.get('file'))

    def test_patch(self):
        uf = self.comment.files.create(
            comment=self.comment,
            name='My first name',
            initial_filename='terminator1.txt',
            file=SimpleUploadedFile('terminator.txt', b'I\'ll be back')
        )
        tmp_file = StringIO('I\'m back')
        tmp_file.name = 'terminator2.txt'

        patch_response = self.client.patch(
            reverse('file-detail',
                    args=[self.request.pk, self.comment.pk, uf.pk]),
            {'file': tmp_file, },
            'multipart'
        )
        self.assertEqual(status.HTTP_200_OK, patch_response.status_code)
        with self.comment.files.get(pk=uf.pk).file.open() as f:
            content = f.read()
            self.assertNotIn(b'I\'ll be back', content)
            self.assertIn(b'I\'m back', content)
        self.assertEqual(uf.name, self.comment.files.get(pk=uf.pk).name)

        patch_response = self.client.patch(
            reverse('file-detail',
                    args=[self.request.pk, self.comment.pk, uf.pk]),
            {'name': 'My new name', }
        )
        self.assertEqual(status.HTTP_200_OK, patch_response.status_code)
        self.assertEqual('My new name', self.comment.files.get(pk=uf.pk).name)

    def test_download(self):
        uf = self.comment.files.create(
            comment=self.comment,
            name='My first name',
            initial_filename='terminator1.txt',
            file=SimpleUploadedFile('terminator.txt', b'I\'ll be back')
        )

        details_response = self.client.get(reverse('file-download',
                                                   args=[self.request.pk,
                                                         self.comment.pk,
                                                         uf.pk]), )
        self.assertEqual(status.HTTP_200_OK,
                         details_response.status_code)
        self.assertEqual('application/octet-stream',
                         details_response.get('Content-Type'))
        self.assertEquals(details_response.get('Content-Disposition'),
                          f'attachment; filename={uf.initial_filename}')
