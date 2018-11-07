from django.urls import reverse
from rest_framework.test import APIClient, APITestCase

from terracommon.accounts.tests.factories import TerraUserFactory
from terracommon.terra.tests.factories import FeatureFactory
from terracommon.tropp.tests.factories import ViewpointFactory
from terracommon.trrequests.tests.mixins import TestPermissionsMixin


class ViewpointTestCase(APITestCase, TestPermissionsMixin):
    def setUp(self):
        self.client = APIClient()

        self.user = TerraUserFactory()

    def test_viewpoint_get_list(self):
        # Create viewpoints with picture attached to it
        ViewpointFactory(label="Test viewpoint creation")
        # TODO Check picture state

        # Create viewpoints with no picture attached to it
        ViewpointFactory(label="Test viewpoint creation", pictures=None)

        # User is not authenticated yet
        data = self.client.get(
            reverse('tropp:viewpoint-list')
        ).json()
        # List must contain all viewpoints WITHOUT those with no pictures
        self.assertEqual(1, data.get('count'))

        # User is now authenticated
        self.client.force_authenticate(user=self.user)
        data = self.client.get(
            reverse('tropp:viewpoint-list')
        ).json()
        # List must still contain ALL viewpoints even those with no pictures
        self.assertEqual(2, data.get('count'))

    def test_viewpoint_get(self):
        viewpoint = ViewpointFactory(label='Test viewpoint get', pictures=None)
        # User is not authenticated yet
        response = self.client.get(
            reverse('tropp:viewpoint-detail', args=[viewpoint.pk])
        )
        # There is no picture on the viewpoint
        self.assertEqual(404, response.status_code)

        # User is now authenticated
        self.client.force_authenticate(user=self.user)
        response = self.client.get(
            reverse('tropp:viewpoint-detail', args=[viewpoint.pk])
        )
        self.assertEqual(200, response.status_code)
        self.assertEqual(response.data.get('label'), viewpoint.label)

    def test_viewpoint_create(self):
        feature = FeatureFactory()
        data = {
            "label": "Test viewpoint creation",
            "point": feature.pk,
        }
        response = self.client.post(
            reverse('tropp:viewpoint-list'),
            data,
        )
        # User is not authenticated
        self.assertEqual(401, response.status_code)

        self.client.force_authenticate(user=self.user)
        response = self.client.post(
            reverse('tropp:viewpoint-list'),
            data,
        )
        # User doesn't have permission
        self.assertEqual(403, response.status_code)

        self._set_permissions(['add_viewpoint', ])
        response = self.client.post(
            reverse('tropp:viewpoint-list'),
            data,
        )
        # Request is correctly constructed and viewpoint has been created
        self.assertEqual(201, response.status_code)

    def test_viewpoint_delete(self):
        viewpoint = ViewpointFactory(label="Test viewpoint creation")

        response = self.client.delete(
            reverse('tropp:viewpoint-detail', args=[viewpoint.pk])
        )
        # User is not authenticated
        self.assertEqual(401, response.status_code)

        self.client.force_authenticate(user=self.user)
        response = self.client.delete(
            reverse('tropp:viewpoint-detail', args=[viewpoint.pk])
        )
        # User doesn't have permission
        self.assertEqual(403, response.status_code)

        self._set_permissions(['delete_viewpoint', ])
        response = self.client.delete(
            reverse('tropp:viewpoint-detail', args=[viewpoint.pk])
        )
        # User have permission
        self.assertEqual(204, response.status_code)
