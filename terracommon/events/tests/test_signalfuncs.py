from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.test import TestCase

from terracommon.accounts.tests.factories import TerraUserFactory
from terracommon.events.signals.funcs import get_user_from_pk, users_of_group

UserModel = get_user_model()


class SingalFuncsTestCase(TestCase):
    def setUp(self):
        self.user = TerraUserFactory()
        self.group = Group.objects.create(name='testgroup')

    def test_get_user_from_pk(self):
        self.assertEqual(
            {'email': self.user.email, 'properties': self.user.properties},
            get_user_from_pk(self.user.pk)
        )

        # Expect an empty return (falsy then) when user does not exist
        self.assertFalse(get_user_from_pk(99999))

    def test_users_of_group(self):
        self.group.user_set.add(self.user)
        expected_result = {
            'email': self.user.email,
            'properties': self.user.properties,
        }
        self.assertIn(expected_result, users_of_group(self.group.name))
