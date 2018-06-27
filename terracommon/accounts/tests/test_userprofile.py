from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient

from terracommon.terra.tests.factories import TerraUserFactory


class RegistrationTestCase(TestCase):
    def setUp(self):
        self.user = TerraUserFactory()
        self.client = APIClient()

    def test_user_profile(self):
        """Tests all operations on user profile
        """

        """unauthenticated user must be stopped"""
        response = self.client.get(reverse('accounts:profile'))
        self.assertEqual(401, response.status_code)

        """let's try with an authenticated user"""
        self.client.force_authenticate(user=self.user)

        response = self.client.get(reverse('accounts:profile'))
        self.assertEqual(200, response.status_code)
        self.assertEqual(str(self.user.uuid), response.json()['uuid'])

        """and try to update the profile"""
        properties = {
            'firstname': 'John',
            'lastname': 'Malkovitch'
        }

        self.client.patch(reverse('accounts:profile'), {
            'properties': properties
        }, format='json')

        self.user.refresh_from_db()
        self.assertDictEqual(properties, self.user.properties)

        """changing e-mail is forbidden"""
        response = self.client.patch(reverse('accounts:profile'), {
            'email': 'john@lennon.com'
        }, format='json')

        old_email = self.user.email
        self.user.refresh_from_db()
        self.assertEqual(200, response.status_code)
        self.assertEqual(old_email, self.user.email)
