from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient

from terracommon.trrequests.models import Comment

from .factories import UserRequestFactory
from .mixins import TestPermissionsMixin


class OrganizationTestCase(TestCase, TestPermissionsMixin):

    def setUp(self):
        self.client = APIClient()

        self.request = UserRequestFactory()
        self.user = self.request.owner
        self.client.force_authenticate(user=self.user)

    def test_comment_creation(self):
        comment_request = {
            'properties': {
                'comment': 'lipsum',
                }
        }
        response = self.client.post(reverse('comment-list',
                                            args=[self.request.pk, ]),
                                    comment_request,
                                    format='json')
        self.assertEqual(403, response.status_code)

        self._set_permissions(['can_comment_requests', ])

        response = self.client.post(reverse('comment-list',
                                            args=[self.request.pk, ]),
                                    comment_request,
                                    format='json')

        self.assertEqual(201, response.status_code)

        response = response.json()

        self.assertTrue(Comment.objects.get(pk=response.get('id')))
        self.assertEqual(self.request.owner.pk,
                         response.get('owner').get('id'))
        self.assertEqual('lipsum', response.get('properties').get('comment'))

        response = self.client.get(reverse('comment-list',
                                           args=[self.request.pk, ]))
        self.assertEqual(200, response.status_code)
        response = response.json()

        """This owner have two organizations, one created in user creation
           process, and one during this test.
        """
        self.assertEqual(1, len(response))
