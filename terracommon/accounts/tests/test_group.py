from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from terracommon.trrequests.tests.mixins import TestPermissionsMixin

from .factories import TerraUserFactory

UserModel = get_user_model()


class UserViewsetTestCase(TestCase, TestPermissionsMixin):
    def setUp(self):
        self.client = APIClient()

        self.group = Group.objects.create(name='test group')

        self.user = TerraUserFactory()
        self.user.groups.add(self.group)

        self.client.force_authenticate(user=self.user)

    def test_group_detail(self):
        response = self.client.get(
            reverse('accounts:group-detail', args=[self.group.pk])
        )

        self.user.refresh_from_db()
        # The user must be in the group
        self.assertIn(self.user.id, response.data['users'])
        # and we must have the group name in the response
        self.assertEqual(self.group.name, response.data['name'])

    def test_create_group(self):
        data = {
            "name": "test group 3"
        }
        response = self.client.post(
            reverse('accounts:group-list'),
            data,
        )
        self.assertEqual(status.HTTP_201_CREATED, response.status_code)
        # We must have only 2 groups in the DB
        self.assertEqual(2, Group.objects.count())
        # And their must be no users in this new group
        self.assertEqual(0, Group.objects.get(name=data["name"]).user_set.count())

    def test_create_group_with_user(self):
        data = {
            "name": "test group 2",
            "users": [self.user.id],
        }
        response = self.client.post(
            reverse('accounts:group-list'),
            data,
        )
        self.user.refresh_from_db()
        self.assertIn(self.user.id, response.data['users'])
        # And also test than the user is in the DB
        self.assertIn(self.user.id, Group.objects.get(name=data["name"]).user_set.values_list('id', flat=True))

    def test_partial_update_name_group(self):
        data = {
            "name": "new group name"
        }
        response = self.client.patch(
            reverse('accounts:group-detail', args=[self.group.pk]),
            data,
        )
        self.assertEqual(status.HTTP_200_OK, response.status_code)
        # We must still have only 1 group in the DB
        self.assertEqual(1, Group.objects.count())
        # but with the new name
        self.assertEqual(data["name"], Group.objects.get(pk=self.group.pk).name)
        # And still have one user in it
        self.assertEqual(1, Group.objects.get(pk=self.group.pk).user_set.count())

    def test_partial_update_user_group(self):
        new_user = TerraUserFactory()
        data = {
            "users": [new_user.id],
        }
        response = self.client.patch(
            reverse('accounts:group-detail', args=[self.group.pk]),
            data,
        )
        self.assertEqual(status.HTTP_200_OK, response.status_code)
        # We must still have only 1 group in the DB
        self.assertEqual(1, Group.objects.count())
        # but with the new user inside
        self.assertIn(new_user.email, Group.objects.get(name=self.group.name).user_set.values_list('email', flat=True))
        # and still have the same name
        self.assertEqual(self.group.name, Group.objects.get(pk=self.group.pk).name)

    def test_update_group_with_new_user(self):
        new_user = TerraUserFactory()
        data = {
            "name": "new group name",
            "users": [new_user.id],
        }
        response = self.client.put(
            reverse('accounts:group-detail', args=[self.group.pk]),
            data,
        )
        self.assertEqual(status.HTTP_200_OK, response.status_code)
        # We must still have only 1 group in the DB
        self.assertEqual(1, Group.objects.count())
        # but with the new name
        self.assertEqual(data["name"], Group.objects.get(name=data["name"]).name)
        # And still have one user in it
        self.assertEqual(1, Group.objects.get(name=data["name"]).user_set.count())
        # but the user should be the new one
        self.assertIn(new_user.email, Group.objects.get(name=data["name"]).user_set.values_list('email', flat=True))

    def test_delete_group(self):
        response = self.client.delete(
            reverse('accounts:group-detail', args=[self.group.pk])
        )
        self.assertEqual(status.HTTP_204_NO_CONTENT, response.status_code)
        self.assertEqual(0, Group.objects.count())
