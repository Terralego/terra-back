import json
from io import StringIO

from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from terracommon.trrequests.models import Comment

from .factories import UserRequestFactory
from .mixins import TestPermissionsMixin


class CommentsTestCase(TestCase, TestPermissionsMixin):

    def setUp(self):
        self.client = APIClient()

        self.request = UserRequestFactory()
        self.user = self.request.owner
        self.client.force_authenticate(user=self.user)

    def test_comment_creation(self):
        comment_request = {
            'is_internal': False,
            'properties': {
                'comment': 'lipsum',
            }
        }

        response = self._post_comment(comment_request)
        self.assertEqual(status.HTTP_403_FORBIDDEN, response.status_code)

        self._set_permissions(['can_comment_requests', ])

        response = self._post_comment(comment_request)
        self.assertEqual(status.HTTP_201_CREATED, response.status_code)

        response = response.json()

        self.assertTrue(Comment.objects.get(pk=response.get('id')))
        self.assertEqual(self.request.owner.pk,
                         response.get('owner').get('id'))
        self.assertEqual('lipsum', response.get('properties').get('comment'))

        """Testing with internal comments"""
        comment_request['is_internal'] = True
        response = self._post_comment(comment_request)
        self.assertFalse(response.json().get('is_internal'))

        """Allow internal comments and test request"""
        self._set_permissions(['can_internal_comment_requests', ])
        response = self._post_comment(comment_request)
        self.assertTrue(response.json().get('is_internal'))

        """And then test what we can retrieve, with internal rights. In this
        test we created 1 internal comment and 2 public comments"""
        """First we test we internal comments allowed"""
        response = self._get_comment_list()
        self.assertEqual(status.HTTP_200_OK, response.status_code)
        response = response.json()
        self.assertEqual(3, response.get('count'))

        """Then with no comment allowed"""
        self._clean_permissions()
        response = self._get_comment_list()
        self.assertEqual(status.HTTP_200_OK, response.status_code)
        response = response.json()
        self.assertEqual(0, response.get('count'))

        """Finally we test with "normal" comment allowed"""
        self._set_permissions(['can_comment_requests', ])
        response = self._get_comment_list()
        self.assertEqual(status.HTTP_200_OK, response.status_code)
        response = response.json()
        self.assertEqual(2, response.get('count'))

    def test_comment_with_attachment(self):
        tmp_file = StringIO('I\'ll be back\n')
        tmp_file.name = 'terminator.txt'
        comment_request = {
            'is_internal': False,
            'properties': json.dumps({
                'comment': 'lorem',
            }),
            'attachment': tmp_file,
        }

        """Post & Permission"""
        response = self._post_comment(comment_request,
                                      format='multipart')
        self.assertEqual(status.HTTP_403_FORBIDDEN, response.status_code)

        tmp_file.seek(0)
        self._set_permissions(['can_comment_requests', ])

        response = self._post_comment(comment_request,
                                      format='multipart')
        self.assertEqual(status.HTTP_201_CREATED, response.status_code)

        response = response.json()
        comment_id = response.get('id')
        self.assertTrue(Comment.objects.get(pk=comment_id))

        comment = Comment.objects.get(pk=comment_id)
        self.assertEqual('lorem', comment.properties.get('comment'))
        comment_attachment = comment.attachment

        """List"""
        response = self._get_comment_list()
        self.assertEqual(status.HTTP_200_OK, response.status_code)
        response = response.json()
        response = list(filter(lambda r: r.get('id', 0) == comment_id,
                               response.get('results', [])))
        self.assertEqual(1, len(response))
        response = response[0]
        self.assertEqual(
            reverse('comment-attachment', args=[self.request.pk, comment_id]),
            response.get('attachment_url'))

        """Patch"""
        response = self._patch_comment(comment_id,
                                       {'properties': {'comment': 'lipsum', }})
        self.assertEqual(status.HTTP_200_OK, response.status_code)
        comment = Comment.objects.get(pk=comment_id)
        self.assertEqual('lipsum', comment.properties.get('comment'))
        self.assertEqual(comment_attachment, comment.attachment)

        tmp_file = StringIO('I\'m back\n')
        tmp_file.name = 'terminator2.txt'
        response = self._patch_comment(comment_id, {'attachment': tmp_file},
                                       format='multipart')
        self.assertEqual(status.HTTP_200_OK, response.status_code)
        comment = Comment.objects.get(pk=comment_id)
        self.assertNotEqual(comment_attachment, comment.attachment)

        """Download"""
        response = self._get_comment_attachment(pk=comment_id)
        self.assertEqual(status.HTTP_200_OK, response.status_code)
        self.assertEquals(f'attachment; filename={tmp_file.name}',
                          response.get('Content-Disposition'))
        self.assertIsNotNone(response.get('X-Accel-Redirect'))

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
