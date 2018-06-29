from django.contrib.auth.tokens import default_token_generator
from django.core import mail
from django.test import TestCase
from django.test.utils import override_settings
from django.urls import reverse
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode

from .factories import TerraUserFactory


class RegistrationTestCase(TestCase):

    @override_settings(
        EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
    def test_registration_view(self):
        response = self.client.post(
            reverse('accounts:register'),
            {
                'email': 'toto@terra.',
            })
        self.assertEqual(400, response.status_code)

        response = self.client.post(
            reverse('accounts:register'),
            {
                'email': 'toto@terra.com',
            })
        self.assertEqual(200, response.status_code)
        self.assertEqual(1, len(mail.outbox))

    def test_reset_password(self):
        user = TerraUserFactory()

        token = default_token_generator.make_token(user)
        uidb64 = urlsafe_base64_encode(force_bytes(user.pk)).decode()

        """Not same password"""
        response = self.client.post(
            reverse('accounts:reset-password', args=[uidb64, token]),
            {
                'new_password1': 'pass1',
                'new_password2': 'pass1false',
            }
        )
        self.assertEqual(400, response.status_code)

        """Good password and """
        new_password = "azerty"
        self.assertFalse(user.check_password(new_password))
        response = self.client.post(
            reverse('accounts:reset-password', args=[uidb64, token]),
            {
                'new_password1': new_password,
                'new_password2': new_password,
            }
        )

        user.refresh_from_db()
        self.assertEqual(200, response.status_code)
        self.assertTrue(user.check_password(new_password))
