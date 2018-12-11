from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.db import IntegrityError
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient

from terracommon.trrequests.tests.mixins import TestPermissionsMixin

from .factories import TerraUserFactory

UserModel = get_user_model()


class UserViewsetTestCase(TestCase, TestPermissionsMixin):
    def setUp(self):
        self.client = APIClient()

        self.user = TerraUserFactory()
        self.client.force_authenticate(user=self.user)

    def test_no_permission(self):
        response = self.client.get(reverse('accounts:user-list')).json()
        # List must be empty with no rights
        self.assertEqual(0, response.get('count'))

    def test_userlist(self):
        self._set_permissions(['can_manage_users', ])
        response = self.client.get(reverse('accounts:user-list')).json()
        # List must contain all database users
        self.assertEqual(UserModel.objects.count(), response.get('count'))

    def test_groups(self):
        group1 = Group.objects.create(name='test group1')
        user = TerraUserFactory()
        user.groups.add(group1)

        group2 = Group.objects.create(name='test group2')
        group3 = Group.objects.create(name='test group3')
        response = self.client.post(
            reverse('accounts:user-groups', args=[user.pk]),
            {
                'groups': [group2.name, group3.name]
            })

        # List must contains same as groups in db
        user.refresh_from_db()
        self.assertListEqual(
            [g.name for g in user.groups.all()],
            response.json())

    def test_create_two_user_with_same_email(self):
        with self.assertRaises(IntegrityError):
            UserModel.objects.create(email=self.user.email)
