import datetime
import json
from io import StringIO

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from terracommon.trrequests.models import Comment

from .factories import CommentFactory, UserRequestFactory
from .mixins import TestPermissionsMixin


class CommentsTestCase(TestCase, TestPermissionsMixin):

    def setUp(self):
        self.client = APIClient()

        self.request = UserRequestFactory()
        self.user = self.request.owner
        self.client.force_authenticate(user=self.user)

    def test_simple_comment_creation_without_permission(self):
        comment_request = {
            'is_internal': False,
            'properties': {
                'comment': 'lipsum',
            }
        }
        response = self._post_comment(comment_request)
        self.assertEqual(status.HTTP_403_FORBIDDEN, response.status_code)

    def test_simple_comment_creation_with_permission(self):
        comment_request = {
            'is_internal': False,
            'properties': {
                'comment': 'lipsum',
            }
        }
        self._set_permissions([
            'can_comment_requests',
        ])
        response = self._post_comment(comment_request)
        self.assertEqual(status.HTTP_201_CREATED, response.status_code)
        response = response.json()
        self.assertTrue(Comment.objects.get(pk=response.get('id')))
        self.assertEqual(self.request.owner.pk,
                         response.get('owner').get('id'))
        self.assertEqual('lipsum', response.get('properties').get('comment'))
        self.assertIsNone(response.get('properties').get('attachment_url'))

    def test_internal_comment_creation_without_internal_permission(self):
        comment_request = {
            'is_internal': True,
            'properties': {
                'comment': 'lipsum',
            }
        }
        response = self._post_comment(comment_request)
        self.assertEqual(status.HTTP_403_FORBIDDEN, response.status_code)
        self.assertFalse(response.json().get('is_internal'))

        # with can_comment permission, user is forbidden to create internal
        # comments
        self._set_permissions([
            'can_comment_requests',
        ])
        response = self._post_comment(comment_request)
        self.assertEqual(status.HTTP_403_FORBIDDEN, response.status_code)
        self.assertFalse(response.json().get('is_internal'))

    def test_internal_comment_creation_with_internal_permission(self):
        comment_request = {
            'is_internal': True,
            'properties': {
                'comment': 'lipsum',
            }
        }
        self._set_permissions([
            'can_internal_comment_requests',
        ])
        response = self._post_comment(comment_request)
        self.assertEqual(status.HTTP_201_CREATED, response.status_code)
        self.assertTrue(response.json().get('is_internal'))

    def test_comment_retrieval_without_permission(self):
        for _ in range(2):
            CommentFactory(userrequest=self.request)
        CommentFactory(userrequest=self.request, is_internal=True)
        response = self._get_comment_list()
        self.assertEqual(status.HTTP_200_OK, response.status_code)
        self.assertEqual(0, response.json().get('count'))

    def test_comment_retrieval_with_normal_permission(self):
        self._set_permissions([
            'can_comment_requests',
        ])
        for _ in range(2):
            CommentFactory(userrequest=self.request)
        CommentFactory(userrequest=self.request,
                       is_internal=True)
        response = self._get_comment_list()
        self.assertEqual(status.HTTP_200_OK, response.status_code)
        self.assertEqual(2, response.json().get('count'))

    def test_comment_retrieval_with_internal_permission(self):
        self._set_permissions([
            'can_comment_requests',
            'can_internal_comment_requests',
        ])
        for _ in range(2):
            CommentFactory(userrequest=self.request)
        CommentFactory(userrequest=self.request, is_internal=True)
        response = self._get_comment_list()
        self.assertEqual(status.HTTP_200_OK, response.status_code)
        self.assertEqual(3, response.json().get('count'))

    def test_comment_with_geojson(self):
        comment_request = {
            'properties': {},
            'geojson': {
                "type": "FeatureCollection",
                "features": [
                    {
                        "type": "Feature",
                        "properties": {},
                        "geometry": {
                            "type": "LineString",
                            "coordinates": [
                                [
                                    2.30712890625,
                                    48.83579746243093
                                ],
                                [
                                    1.42822265625,
                                    43.628123412124616
                                ]
                            ]
                        }
                    },
                ]
            }
        }

        self._set_permissions([
            'can_comment_requests',
        ])
        response = self._post_comment(comment_request)

        self.assertEqual(status.HTTP_201_CREATED, response.status_code)
        response = response.json()
        self.assertIsNotNone(response.get('geojson'))

    def test_comment_creation_with_attachment(self):
        tmp_file = StringIO('File content')
        tmp_file.name = 'filename.txt'
        comment_request = {
            'is_internal': False,
            'properties': json.dumps({
                'comment': 'lipsum',
            }),
            'attachment': tmp_file,
        }
        self._set_permissions([
            'can_comment_requests',
        ])
        response = self._post_comment(comment_request, format='multipart')
        self.assertEqual(status.HTTP_201_CREATED, response.status_code)
        comment_updated = Comment.objects.get(pk=response.json().get('id'))
        self.assertEqual('lipsum', comment_updated.properties.get('comment'))
        self.assertIsNotNone(comment_updated.attachment)
        self.assertIn(f'comment_{datetime.date.today():%d}',
                      comment_updated.attachment.url)
        self.assertEqual(tmp_file.name, comment_updated.filename)
        self.assertNotEqual(tmp_file.name, comment_updated.attachment.name)

    def test_comment_creations_with_same_filename(self):
        tmp_file = StringIO('File content')
        tmp_file.name = 'filename.txt'
        comment_request = {
            'is_internal': False,
            'attachment': tmp_file,
        }
        self._set_permissions([
            'can_comment_requests',
        ])
        # Comment 1
        comment1_request = comment_request.copy()
        comment1_request['properties'] = json.dumps({
            'comment': 'lorem',
        })
        response1 = self._post_comment(comment1_request, format='multipart')
        self.assertEqual(status.HTTP_201_CREATED, response1.status_code)
        comment1_updated = Comment.objects.get(pk=response1.json().get('id'))
        self.assertIsNotNone(comment1_updated.attachment)
        # Comment 2
        tmp_file.seek(0)
        comment2_request = comment_request.copy()
        comment2_request['properties'] = json.dumps({
            'comment': 'lorem',
        })
        response2 = self._post_comment(comment2_request, format='multipart')
        self.assertEqual(status.HTTP_201_CREATED, response2.status_code)
        comment2_updated = Comment.objects.get(pk=response2.json().get('id'))
        self.assertIsNotNone(comment2_updated.attachment)

        self.assertNotEqual(comment1_updated.attachment.url,
                            comment2_updated.attachment.url)

    def test_download_comment_attachment(self):
        tmp_file = SimpleUploadedFile('filename.txt', b'File content')
        comment = CommentFactory(userrequest=self.request,
                                 attachment=tmp_file)
        self._set_permissions([
            'can_comment_requests',
        ])
        response = self._get_comment_attachment(pk=comment.pk)
        self.assertEqual(status.HTTP_200_OK, response.status_code)
        self.assertEquals(f'attachment; filename={tmp_file.name}',
                          response.get('Content-Disposition'))
        self.assertIsNotNone(response.get('X-Accel-Redirect'))

    def test_update_simple_comment_properties(self):
        comment = CommentFactory(userrequest=self.request,
                                 attachment=SimpleUploadedFile(
                                     'filename.txt',
                                     b'File content'
                                 ))
        comment_request = {
            'properties': {
                'comment': 'Hello world',
            },
        }
        self._set_permissions([
            'can_comment_requests',
        ])
        response = self._patch_comment(comment.pk, comment_request)
        # Update is forbidden for all users
        self.assertEqual(status.HTTP_405_METHOD_NOT_ALLOWED,
                         response.status_code)

    def test_delete_comment(self):
        comment = CommentFactory(userrequest=self.request)
        self._set_permissions([
            'can_comment_requests',
            'can_internal_comment_requests',
        ])
        response = self.client.delete(
            reverse('comment-detail', args=[self.request.pk, comment.pk]),
            format=format)
        # Delete a comment is forbidden
        self.assertEqual(status.HTTP_405_METHOD_NOT_ALLOWED,
                         response.status_code)

    def test_attachment_url_value(self):
        c = CommentFactory(userrequest=self.request,
                           attachment=SimpleUploadedFile(
                               'filename.txt',
                               b'File content'
                           ))
        self._set_permissions([
            'can_comment_requests',
        ])
        response = self._get_comment_list()
        self.assertEqual(1, response.json().get('count'))
        comment_recovered = list(filter(lambda r: r.get('id', 0) == c.pk,
                                        response.json().get('results', [])))
        self.assertEqual(1, len(comment_recovered))
        response = comment_recovered[0]
        self.assertEqual(
            reverse('comment-attachment', args=[self.request.pk, c.pk]),
            response.get('attachment_url'))

    def _get_comment_list(self):
        return self.client.get(
            reverse('comment-list', args=[self.request.pk, ]))

    def _post_comment(self, comment, format='json'):
        return self.client.post(reverse('comment-list',
                                        args=[self.request.pk, ]),
                                comment,
                                format=format)

    def _patch_comment(self, pk, comment, format='json'):
        return self.client.patch(reverse('comment-detail',
                                         args=[self.request.pk, pk]),
                                 comment,
                                 format=format)

    def _get_comment_attachment(self, pk):
        return self.client.get(reverse('comment-attachment',
                                       args=[self.request.pk, pk]))
