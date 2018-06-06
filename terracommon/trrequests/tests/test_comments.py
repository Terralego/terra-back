from django.test import TestCase
from django.urls import reverse
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
        self.assertEqual(403, response.status_code)

        self._set_permissions(['can_comment_requests', ])

        response = self._post_comment(comment_request)
        self.assertEqual(201, response.status_code)

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
        response = self.client.get(
            reverse('comment-list', args=[self.request.pk, ]))
        self.assertEqual(200, response.status_code)
        response = response.json()
        self.assertEqual(3, len(response))

        """Then with no comment allowed"""
        self._clean_permissions()
        response = self.client.get(
            reverse('comment-list', args=[self.request.pk, ]))
        self.assertEqual(200, response.status_code)
        response = response.json()
        self.assertEqual(0, len(response))

        """Finally we test with "normal" comment allowed"""
        self._set_permissions(['can_comment_requests', ])
        response = self.client.get(
            reverse('comment-list', args=[self.request.pk, ]))
        self.assertEqual(200, response.status_code)
        response = response.json()
        self.assertEqual(2, len(response))


    def _post_comment(self, comment):
        return self.client.post(reverse('comment-list',
                                        args=[self.request.pk, ]),
                                comment,
                                format='json')