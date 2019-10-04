from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from terra_accounts.tests.factories import TerraUserFactory
from terra_utils.settings import STATES

from terracommon.trrequests.models import UserRequest

from .factories import CommentFactory, UserRequestFactory
from .mixins import TestPermissionsMixin


class ReadableUserRequestTestCase(TestCase, TestPermissionsMixin):
    def setUp(self):
        self.client = APIClient()

        self.user = TerraUserFactory()
        self._set_permissions(['can_read_self_requests', ])
        self.client.force_authenticate(user=self.user)

    def test_nocomment_and_unread(self):
        userrequest = UserRequestFactory(owner=self.user)
        response = self.client.get(
            reverse('trrequests:request-detail', args=[userrequest.pk, ])
        ).json()

        self.assertFalse(response['has_new_comments'])
        self.assertTrue(response['has_new_changes'])

    def test_unread_comments(self):
        self._set_permissions(['can_read_comment_requests', ])

        userrequest = UserRequestFactory(owner=self.user)
        CommentFactory(userrequest=userrequest)
        userrequest.user_read(self.user)

        # one comment but no changes to userrequest
        response = self.client.get(
            reverse('trrequests:request-detail', args=[userrequest.pk, ])
        ).json()

        self.assertFalse(response['has_new_comments'])
        self.assertFalse(response['has_new_changes'])

        # new unread comment
        userrequest.user_read(self.user)
        CommentFactory(userrequest=userrequest)
        response = self.client.get(
            reverse('trrequests:request-detail', args=[userrequest.pk, ])
        ).json()

        self.assertTrue(response['has_new_comments'])
        self.assertFalse(response['has_new_changes'])

        # new internal comment but no rights
        userrequest.user_read(self.user)
        CommentFactory(userrequest=userrequest, is_internal=True)
        response = self.client.get(
            reverse('trrequests:request-detail', args=[userrequest.pk, ])
        ).json()

        self.assertFalse(response['has_new_comments'])
        self.assertFalse(response['has_new_changes'])

        self._clean_permissions()

    def test_new_changes(self):
        # new userrequest, never read
        userrequest = UserRequestFactory(owner=self.user)
        response = self.client.get(
            reverse('trrequests:request-detail', args=[userrequest.pk, ])
        ).json()

        self.assertTrue(response['has_new_changes'])

        # read once through API
        response = self.client.get(
            reverse('trrequests:request-read', args=[userrequest.pk, ]))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json().get('id'), userrequest.pk)

        response = self.client.get(
            reverse('trrequests:request-detail', args=[userrequest.pk, ])
        ).json()

        self.assertFalse(response['has_new_changes'])

        # lets make a change to the userrequest
        userrequest.save()
        response = self.client.get(
            reverse('trrequests:request-detail', args=[userrequest.pk, ])
        ).json()

        self.assertTrue(response['has_new_changes'])

    def test_userrequest_and_comment_creation_read(self):
        request = {
            'properties': {
                'myproperty': 'myvalue',
            },
            'geojson': {},
        }

        self._set_permissions(['can_create_requests', ])
        response = self.client.post(reverse('trrequests:request-list'),
                                    request,
                                    format='json')
        ur = UserRequest.objects.get(pk=response.json()['id'])
        read_object = ur.get_user_read(self.user)
        self.assertIsNotNone(read_object)
        read_object.delete()

        # test update
        response = self.client.patch(
                    reverse('trrequests:request-detail', args=[ur.pk, ]),
                    request,
                    format='json')
        read_object = ur.get_user_read(self.user)
        self.assertIsNotNone(read_object)
        read_object.delete()

        # test comment
        comment_request = {
            'is_internal': False,
            'properties': {
                'comment': 'lipsum',
            }
        }
        self._set_permissions([
            'can_comment_requests',
        ])
        response = self.client.post(reverse('trrequests:comment-list',
                                    args=[ur.pk, ]),
                                    comment_request,
                                    format='json')

        self.assertEqual(status.HTTP_201_CREATED, response.status_code)
        read_object = ur.get_user_read(self.user)
        self.assertIsNotNone(read_object)

    def test_userrequest_draft_only_read_by_owner(self):
        self._set_permissions(['can_read_all_requests', ])

        # test with a non owner user
        UserRequestFactory(state=STATES.DRAFT)
        response = self.client.get(reverse('trrequests:request-list'))

        self.assertEqual(status.HTTP_200_OK, response.status_code)
        self.assertEqual(response.json().get('count'), 0)

        self._clean_permissions()

        # # test with a owner
        UserRequestFactory(state=STATES.DRAFT, owner=self.user)

        self._set_permissions(['can_read_self_requests', ])

        response = self.client.get(reverse('trrequests:request-list'))
        self.assertEqual(status.HTTP_200_OK, response.status_code)
        self.assertNotEqual(response.json().get('count'), 0)

        self._clean_permissions()
