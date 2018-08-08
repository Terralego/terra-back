from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from .factories import TerraUserFactory


class ChangePasswordTestCase(TestCase):
    def setUp(self):
        self.user = TerraUserFactory()
        self.client = APIClient()
        self.client.login(email=self.user.email, password='123456')

    def test_change_password(self):
        response = self.client.post(
            reverse('accounts:new-password'),
            {
                'old_password': '123456',
                'new_password1': '654321',
                'new_password2': '654321',
            }
        )
        self.assertEqual(status.HTTP_200_OK, response.status_code)
        self.user.refresh_from_db()
        self.assertFalse(self.user.check_password('123456'))
        self.assertTrue(self.user.check_password('654321'))

    def test_change_password_not_same(self):
        response = self.client.post(
            reverse('accounts:new-password'),
            {
                'old_password': '123456',
                'new_password1': '654321',
                'new_password2': '654123',
            }
        )
        self.assertEqual(status.HTTP_400_BAD_REQUEST, response.status_code)
        self.user.refresh_from_db()
        self.assertFalse(self.user.check_password('654321'))
        self.assertFalse(self.user.check_password('654123'))
        self.assertTrue(self.user.check_password('123456'))

    def test_change_password_wrong_old_password(self):
        response = self.client.post(
            reverse('accounts:new-password'),
            {
                'old_password': '654321',
                'new_password1': 'whocares',
                'new_password2': 'whocares',
            }
        )
        self.assertEqual(status.HTTP_400_BAD_REQUEST, response.status_code)
        self.user.refresh_from_db()
        self.assertFalse(self.user.check_password('654321'))
        self.assertFalse(self.user.check_password('whocares'))

    def test_change_password_missing_confirmation_password(self):
        response = self.client.post(
            reverse('accounts:new-password'),
            {
                'old_password': '123456',
                'new_password1': '654321',
            }
        )
        self.assertEqual(status.HTTP_400_BAD_REQUEST, response.status_code)
        self.user.refresh_from_db()
        self.assertFalse(self.user.check_password('654321'))
        self.assertTrue(self.user.check_password('123456'))

    def test_change_password_without_authentication(self):
        self.client.logout()
        response = self.client.post(
            reverse('accounts:new-password'),
            {
                'old_password': '123456',
                'new_password1': '654321',
                'new_password2': '654321',
            }
        )
        self.assertEqual(status.HTTP_401_UNAUTHORIZED, response.status_code)
        self.user.refresh_from_db()
        self.assertFalse(self.user.check_password('654321'))
        self.assertTrue(self.user.check_password('123456'))
