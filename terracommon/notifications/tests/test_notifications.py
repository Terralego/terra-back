from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from .factories import UserFactory


class NotificationsTestCase(TestCase):
    def setUp(self):
        self.user = UserFactory()
        self.client = APIClient()
        self.client.force_login(self.user)

    def test_read_all(self):

        self.user.notifications.create(
            level='WARNING',
            event_code='test_code',
            identifier=42,
            read=False,
        )

        response = self.client.get(
            reverse('notifications:notifications-read-all'))

        self.assertEqual(status.HTTP_200_OK, response.status_code)
        self.assertTrue(self.user.notifications.first().read)
