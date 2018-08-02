from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from .factories import TerraUserFactory


class ChangePasswordTestCase(TestCase):
    def setUp(self):
        self.user = TerraUserFactory()
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    def test_change_password(self):
        old_pass = self.user.password
        response = self.client.post(
            reverse('accounts:new-password'),
            {
                'old_password': '123456',
                'new_password1': '654321',
                'new_password2': '654321',
            }
        )
        self.assertEqual(status.HTTP_200_OK, response.status_code)
        self.assertNotEqual(old_pass, self.user.password)

    def test_change_password_not_same(self):
        old_pass = self.user.password
        response = self.client.post(
            reverse('accounts:new-password'),
            {
                'old_password': '123456',
                'new_password1': '654321',
                'new_password2': '654123',
            }
        )
        self.assertEqual(status.HTTP_400_BAD_REQUEST, response.status_code)
        self.assertEqual(old_pass, self.user.password)

    def test_change_password_wrong_old_password(self):
        response = self.client.post(
            reverse('accounts:new-password'),
            {
                'old_password': '654321',
                'new_password1': 'whocares',
                'new_password2': 'whocares',
            }
        )
        old_pass = self.user.password
        self.assertEqual(status.HTTP_400_BAD_REQUEST, response.status_code)
        self.assertEqual(old_pass, self.user.password)

    def test_change_password_missing_confirmation_password(self):
        old_pass = self.user.password
        response = self.client.post(
            reverse('accounts:new-password'),
            {
                'old_password': '123456',
                'new_password1': '654321',
            }
        )
        self.assertEqual(status.HTTP_400_BAD_REQUEST, response.status_code)
        self.assertEqual(old_pass, self.user.password)

    def test_change_password_without_authentication(self):
        old_pass = self.user.password
        self.client.force_authenticate(user=None)
        response = self.client.post(
            reverse('accounts:new-password'),
            {
                'old_password': '123456',
                'new_password1': '654321',
                'new_password2': '654321',
            }
        )
        self.assertEqual(status.HTTP_401_UNAUTHORIZED, response.status_code)
        self.assertEqual(old_pass, self.user.password)
