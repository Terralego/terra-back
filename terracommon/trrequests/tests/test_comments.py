from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient

from terracommon.trrequests.models import Comment
from terracommon.trrequests.tests.factories import UserRequestFactory


class OrganizationTestCase(TestCase):

    def setUp(self):
        self.client = APIClient()

        self.request = UserRequestFactory()
        self.client.force_authenticate(user=self.request.owner)

    def test_organization_creation(self):
        response = self.client.post(reverse('comment-list', args=[self.request.pk, ]),
        {
            'properties': {
                'comment': 'lipsum',
            }
        }, format='json')

        self.assertEqual(201, response.status_code)

        response = response.json()
        comment = Comment.objects.get(pk=response.get('id'))
        
        self.assertEqual(self.request.owner.pk, response.get('owner').get('id'))
        self.assertEqual('lipsum', response.get('properties').get('comment'))

        response = self.client.get(reverse('comment-list', args=[self.request.pk, ]))
        self.assertEqual(200, response.status_code)
        response = response.json()

        """This owner have two organizations, one created in user creation 
           process, and one during this test.
        """
        self.assertEqual(1, len(response))
