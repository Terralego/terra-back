from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from terracommon.accounts.tests.factories import TerraUserFactory

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
            reverse('request-detail', args=[userrequest.pk, ])).json()

        self.assertFalse(response['has_new_comments'])
        self.assertTrue(response['has_new_changes'])

    def test_unread_comments(self):
        userrequest = UserRequestFactory(owner=self.user)
        CommentFactory(userrequest=userrequest)
        userrequest.user_read(self.user)

        # one comment but new changes to userrequest
        response = self.client.get(
            reverse('request-detail', args=[userrequest.pk, ])).json()

        self.assertFalse(response['has_new_comments'])
        self.assertFalse(response['has_new_changes'])

        # new unread comment
        userrequest.user_read(self.user)
        CommentFactory(userrequest=userrequest)
        response = self.client.get(
            reverse('request-detail', args=[userrequest.pk, ])).json()

        self.assertTrue(response['has_new_comments'])
        self.assertFalse(response['has_new_changes'])

    def test_new_changes(self):
        # new userrequest, never read
        userrequest = UserRequestFactory(owner=self.user)
        response = self.client.get(
            reverse('request-detail', args=[userrequest.pk, ])).json()

        self.assertTrue(response['has_new_changes'])

        # read once through API
        response = self.client.get(
            reverse('request-read', args=[userrequest.pk, ]))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response = self.client.get(
            reverse('request-detail', args=[userrequest.pk, ])).json()

        self.assertFalse(response['has_new_changes'])

        # lets make a change to the userrequest
        userrequest.save()
        response = self.client.get(
            reverse('request-detail', args=[userrequest.pk, ])).json()

        self.assertTrue(response['has_new_changes'])
