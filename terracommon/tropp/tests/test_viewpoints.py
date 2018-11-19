import os
from datetime import timedelta

from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from terracommon.accounts.tests.factories import TerraUserFactory
from terracommon.core.settings import STATES
from terracommon.terra.tests.factories import FeatureFactory
from terracommon.tropp.tests.factories import ViewpointFactory
from terracommon.trrequests.tests.mixins import TestPermissionsMixin


class ViewpointTestCase(APITestCase, TestPermissionsMixin):
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

    def test_viewpoint_get_list_anonymous(self):
        data = self.client.get(
            reverse('tropp:viewpoints-list')
        ).json()
        # List must contain all viewpoints WITHOUT those with no pictures
        # Pictures must also be ACCEPTED
        self.assertEqual(1, data.get('count'))

    def test_viewpoint_get_list_with_auth(self):
        # User is now authenticated
        self.client.force_authenticate(user=self.user)
        data = self.client.get(
            reverse('tropp:viewpoints-list')
        ).json()
        # List must still contain ALL viewpoints even those with no
        # pictures and pictures with other states than ACCEPTED
        self.assertEqual(3, data.get('count'))

    def test_viewpoint_get_anonymous(self):
        # User is not authenticated yet
        response = self.client.get(
            reverse(
                'tropp:viewpoints-detail',
                args=[self.viewpoint_without_picture.pk],
            )
        )
        # There is no picture on the viewpoint
        self.assertEqual(status.HTTP_404_NOT_FOUND, response.status_code)

    def test_viewpoint_get_with_auth(self):
        # User is now authenticated
        self.client.force_authenticate(user=self.user)
        response = self.client.get(
            reverse(
                'tropp:viewpoints-detail',
                args=[self.viewpoint_without_picture.pk],
            )
        )
        self.assertEqual(status.HTTP_200_OK, response.status_code)

    def test_viewpoint_search(self):
        # Quick test for the simple viewpoint search feature
        data = self.client.get(
            reverse('tropp:viewpoints-list'),
            {'search': self.viewpoint_with_accepted_picture.pk},
        ).json()
        self.assertEqual(data.get('count'), 1)

        search_options_url = reverse('tropp:viewpoints-search-options')
        data = self.client.get(search_options_url).json()
        self.assertNotEqual(data.get('viewpoints'), [])
        self.assertIsNone(data.get('themes'))
        self.assertIsNone(data.get('photographers'))

    def test_viewpoint_picture_filter(self):
        # Quick test for the simple viewpoint search feature
        data = self.client.get(
            reverse('tropp:viewpoints-list'),
            {'picture_id': self.viewpoint_with_accepted_picture.pictures
                .first().pk},
        ).json()
        self.assertEqual(data.get('count'), 1)

    def test_viewpoint_photographer_filter(self):
        # Quick test for the simple viewpoint search feature
        picture = self.viewpoint_with_accepted_picture.pictures.first()
        data = self.client.get(
            reverse('tropp:viewpoints-list'),
            {'photographer': picture.owner.email},
        ).json()
        self.assertEqual(data.get('count'), 1)

    def test_viewpoint_search_date(self):
        list_url = reverse('tropp:viewpoints-list')
        picture = self.viewpoint_with_accepted_picture.pictures.first()
        data = self.client.get(
            list_url,
            {'date_from': (picture.date - timedelta(days=1)).date()}
        ).json()
        self.assertEqual(data.get('count'), 1)
        data = self.client.get(
            list_url,
            {'date_from': (picture.date + timedelta(days=1)).date()}
        ).json()
        self.assertEqual(data.get('count'), 0)
        data = self.client.get(
            list_url,
            {'date_to': (picture.date + timedelta(days=1)).date()}
        ).json()
        self.assertEqual(data.get('count'), 1)
        data = self.client.get(
            list_url,
            {'date_to': (picture.date - timedelta(days=1)).date()}
        ).json()
        self.assertEqual(data.get('count'), 0)
        data = self.client.get(
            list_url,
            {
                'date_from': (picture.date - timedelta(days=1)).date(),
                'date_to': (picture.date + timedelta(days=1)).date(),
            }
        ).json()
        self.assertEqual(data.get('count'), 1)

        # Errors
        response = self.client.get(
            list_url,
            {
                'date_from': (picture.date + timedelta(days=1)).date(),
                'date_to': (picture.date - timedelta(days=1)).date(),
            }
        )
        self.assertEqual(status.HTTP_400_BAD_REQUEST, response.status_code)
        response = self.client.get(
            list_url,
            {'date_to': 'haha'}
        )
        self.assertEqual(status.HTTP_400_BAD_REQUEST, response.status_code)

    def _viewpoint_create(self):
        return self.client.post(
            reverse('tropp:viewpoints-list'),
            self.data_create,
        )

    def test_viewpoint_create_anonymous(self):
        response = self._viewpoint_create()
        # User is not authenticated
        self.assertEqual(status.HTTP_401_UNAUTHORIZED, response.status_code)

    def test_viewpoint_create_with_auth(self):
        self.client.force_authenticate(user=self.user)
        response = self._viewpoint_create()
        # User doesn't have permission
        self.assertEqual(status.HTTP_403_FORBIDDEN, response.status_code)

    def test_viewpoint_create_with_auth_and_perms(self):
        self.client.force_authenticate(user=self.user)
        self._set_permissions(['add_viewpoint', ])
        response = self._viewpoint_create()
        # Request is correctly constructed and viewpoint has been created
        self.assertEqual(status.HTTP_201_CREATED, response.status_code)
        self._clean_permissions()  # Don't forget that !

    def _viewpoint_create_with_picture(self):
        return self.client.post(
            reverse('tropp:viewpoints-list'),
            self.data_create_with_picture,
            format="multipart",
        )

    def test_viewpoint_create_with_picture_anonymous(self):
        response = self._viewpoint_create_with_picture()
        # User is not authenticated
        self.assertEqual(status.HTTP_401_UNAUTHORIZED, response.status_code)

    def test_viewpoint_create_with_picture_with_auth(self):
        self.client.force_authenticate(user=self.user)
        response = self._viewpoint_create_with_picture()
        # User doesn't have permission
        self.assertEqual(status.HTTP_403_FORBIDDEN, response.status_code)

    def test_viewpoint_create_with_picture_with_auth_and_perms(self):
        self.client.force_authenticate(user=self.user)
        self._set_permissions(['add_viewpoint', ])
        response = self._viewpoint_create_with_picture()
        # Request is correctly constructed and viewpoint has been created
        self.assertEqual(status.HTTP_201_CREATED, response.status_code)
        self._clean_permissions()

    def _viewpoint_delete(self):
        return self.client.delete(
            reverse('tropp:viewpoints-detail', args=[self.viewpoint.pk])
        )

    def test_viewpoint_delete_anonymous(self):
        response = self._viewpoint_delete()
        # User is not authenticated
        self.assertEqual(status.HTTP_401_UNAUTHORIZED, response.status_code)

    def test_viewpoint_delete_with_auth(self):
        self.client.force_authenticate(user=self.user)
        response = self._viewpoint_delete()
        # User doesn't have permission
        self.assertEqual(status.HTTP_403_FORBIDDEN, response.status_code)

    def test_viewpoint_delete_with_auth_and_perms(self):
        self.client.force_authenticate(user=self.user)
        self._set_permissions(['delete_viewpoint', ])
        response = self._viewpoint_delete()
        # User have permission
        self.assertEqual(status.HTTP_204_NO_CONTENT, response.status_code)
        self._clean_permissions()
