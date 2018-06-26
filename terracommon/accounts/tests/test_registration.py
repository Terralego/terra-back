from django.core import mail
from django.test import TestCase
from django.test.utils import override_settings
from django.urls import reverse


class RegistrationTestCase(TestCase):

    @override_settings(
        EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
    def test_registration_view(self):
        response = self.client.post(
            reverse('accounts-register'),
            {
                'email': 'toto@terra.',
            })
        self.assertEqual(400, response.status_code)

        response = self.client.post(
            reverse('accounts-register'),
            {
                'email': 'toto@terra.com',
            })
        self.assertEqual(200, response.status_code)
        self.assertEqual(1, len(mail.outbox))
