import os

from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APIClient, APITestCase

from terracommon.accounts.tests.factories import TerraUserFactory
from terracommon.core.settings import STATES
from terracommon.terra.tests.factories import FeatureFactory
from terracommon.tropp.tests.factories import ViewpointFactory
from terracommon.trrequests.tests.mixins import TestPermissionsMixin


class ViewpointTestCase(APITestCase, TestPermissionsMixin):
    client_class = APIClient

    @classmethod
    def setUpTestData(cls):
        cls.feature = FeatureFactory()
        cls.user = TerraUserFactory()
        # Create viewpoint with draft picture attached to it
        cls.viewpoint = ViewpointFactory(label="Basic viewpoint")
        # Create viewpoint with accepted picture attached to it
        cls.viewpoint_with_accepted_picture = ViewpointFactory(
            label="Viewpoint with accepted picture",
            pictures__state=STATES.ACCEPTED,
        )
        # Create viewpoints with no picture attached to it
        cls.viewpoint_without_picture = ViewpointFactory(
            label="Viewpoint without picture",
            pictures=None
        )

    def setUp(self):
        self.fp = open(
            os.path.join(os.path.dirname(__file__), 'placeholder.jpg'),
            'rb',
        )
        date = timezone.datetime(2018, 1, 1, tzinfo=timezone.utc)
        self.data_create = {
            "label": "Basic viewpoint created",
            "point": self.feature.pk,
        }
        self.data_create_with_picture = {
            "label": "Viewpoint created with picture",
            "point": self.feature.pk,
            # Cannot have nested json when working on files
            "picture.date": date,
            "picture.file": self.fp,
        }

    def tearDown(self):
        self.fp.close()

    def test_viewpoint_get_list_with_no_auth(self):
        # User is not authenticated yet
        data = self.client.get(
            reverse('tropp:viewpoint-list')
        ).json()
        # List must contain all viewpoints WITHOUT those with no pictures
        # Pictures must also be ACCEPTED
        self.assertEqual(1, data.get('count'))

    def test_viewpoint_get_list_with_auth(self):
        # User is now authenticated
        self.client.force_authenticate(user=self.user)
        data = self.client.get(
            reverse('tropp:viewpoint-list')
        ).json()
        # List must still contain ALL viewpoints even those with no pictures
        #  and pictures with other states than ACCEPTED
        self.assertEqual(3, data.get('count'))

    def test_viewpoint_get_with_no_auth(self):
        # User is not authenticated yet
        response = self.client.get(
            reverse(
                'tropp:viewpoint-detail',
                args=[self.viewpoint_without_picture.pk],
            )
        )
        # There is no picture on the viewpoint
        self.assertEqual(404, response.status_code)

    def test_viewpoint_get_with_auth(self):
        # User is now authenticated
        self.client.force_authenticate(user=self.user)
        response = self.client.get(
            reverse(
                'tropp:viewpoint-detail',
                args=[self.viewpoint_without_picture.pk],
            )
        )
        self.assertEqual(200, response.status_code)
        self.assertEqual(
            response.data.get('label'),
            self.viewpoint_without_picture.label,
        )

    def test_viewpoint_create_with_no_auth(self):
        response = self.client.post(
            reverse('tropp:viewpoint-list'),
            self.data_create,
        )
        # User is not authenticated
        self.assertEqual(401, response.status_code)

    def test_viewpoint_create_with_auth(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.post(
            reverse('tropp:viewpoint-list'),
            self.data_create,
        )
        # User doesn't have permission
        self.assertEqual(403, response.status_code)

    def test_viewpoint_create_with_auth_and_perms(self):
        self.client.force_authenticate(user=self.user)
        self._set_permissions(['add_viewpoint', ])
        response = self.client.post(
            reverse('tropp:viewpoint-list'),
            self.data_create,
        )
        # Request is correctly constructed and viewpoint has been created
        self.assertEqual(201, response.status_code)
        self._clean_permissions()  # Don't forget that !

    def test_viewpoint_create_with_picture_with_no_auth(self):
        response = self.client.post(
            reverse('tropp:viewpoint-list'),
            self.data_create_with_picture,
            format="multipart",
        )
        # User is not authenticated
        self.assertEqual(401, response.status_code)

    def test_viewpoint_create_with_picture_with_auth(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.post(
            reverse('tropp:viewpoint-list'),
            self.data_create_with_picture,
            format="multipart",
        )
        # User doesn't have permission
        self.assertEqual(403, response.status_code)

    def test_viewpoint_create_with_picture_with_auth_and_perms(self):
        self.client.force_authenticate(user=self.user)
        self._set_permissions(['add_viewpoint', ])
        response = self.client.post(
            reverse('tropp:viewpoint-list'),
            self.data_create_with_picture,
            format="multipart",
        )
        # Request is correctly constructed and viewpoint has been created
        self.assertEqual(201, response.status_code)
        self._clean_permissions()

    def test_viewpoint_delete_with_no_auth(self):
        response = self.client.delete(
            reverse('tropp:viewpoint-detail', args=[self.viewpoint.pk])
        )
        # User is not authenticated
        self.assertEqual(401, response.status_code)

    def test_viewpoint_delete_with_auth(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.delete(
            reverse('tropp:viewpoint-detail', args=[self.viewpoint.pk])
        )
        # User doesn't have permission
        self.assertEqual(403, response.status_code)

    def test_viewpoint_delete_with_auth_and_perms(self):
        self.client.force_authenticate(user=self.user)
        self._set_permissions(['delete_viewpoint', ])
        response = self.client.delete(
            reverse('tropp:viewpoint-detail', args=[self.viewpoint.pk])
        )
        # User have permission
        self.assertEqual(204, response.status_code)
        self._clean_permissions()
