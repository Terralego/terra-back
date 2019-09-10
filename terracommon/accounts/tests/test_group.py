from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient

from terracommon.trrequests.tests.mixins import TestPermissionsMixin

from .factories import TerraUserFactory

UserModel = get_user_model()


class UserViewsetTestCase(TestCase, TestPermissionsMixin):
    def setUp(self):
        self.client = APIClient()

        self.group = Group.objects.create(name='test group')

        self.user = TerraUserFactory()
        self.client.force_authenticate(user=self.user)

    def test_group_detail_returns_users(self):
        self.user.groups.add(self.group)

        response = self.client.get(
            reverse('accounts:group-detail', args=[self.group.pk])
        )

        self.user.refresh_from_db()
        self.assertIn(self.user.id, response.data['users'])

    def test_group_update_with_user(self):
        response = self.client.post(
            reverse('accounts:group-list'),
            {
                "name": "test group 2",
                "users": [self.user.id],
            }
        )

        self.user.refresh_from_db()
        self.assertIn(self.user.id, response.data['users'])
        # And also test than the user is in the DB
        self.assertIn(self.user.id, Group.objects.get(name="test group 2").user_set.values_list('id', flat=True))
