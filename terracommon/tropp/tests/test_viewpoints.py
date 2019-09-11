import os
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings
from django.urls import reverse
from django.utils import timezone
from geostore.models import Feature
from geostore.tests.factories import FeatureFactory
from rest_framework import status
from rest_framework.test import APITestCase

from terracommon.accounts.tests.factories import TerraUserFactory
from terracommon.core.settings import STATES
from terracommon.tropp.models import Picture, Viewpoint
from terracommon.tropp.tests.factories import ViewpointFactory
from terracommon.trrequests.tests.mixins import TestPermissionsMixin


class ViewpointTestCase(APITestCase, TestPermissionsMixin):
    @classmethod
    @override_settings(TROPP_PICTURES_STATES_WORKFLOW=True)
    def setUpTestData(cls):
        cls.feature = FeatureFactory()
        cls.user = TerraUserFactory()
        # Create viewpoint with draft picture attached to it
        cls.viewpoint = ViewpointFactory(label="Basic viewpoint")
        # Create viewpoint with accepted picture attached to it
        cls.viewpoint_with_accepted_picture = ViewpointFactory(
            label="Viewpoint with accepted picture",
            pictures__state=STATES.ACCEPTED,
            properties={'test_update': 'ko'},
        )
        # Create viewpoints with no picture attached to it
        cls.viewpoint_without_picture = ViewpointFactory(
            label="Viewpoint without picture",
            pictures=None,
            properties={'test_update': 'ko'},
        )

    def setUp(self):
        self.fp = open(
            os.path.join(os.path.dirname(__file__), 'placeholder.jpg'),
            'rb',
        )
        date = timezone.datetime(2018, 1, 1, tzinfo=timezone.utc)
        self.data_create = {
            "label": "Basic viewpoint created",
            "point": self.feature.geom.json,
        }
        self.data_create_with_picture = {
            "label": "Viewpoint created with picture",
            "point": self.feature.geom.json,
            # Cannot have nested json when working on files
            "picture.date": date,
            "picture.file": self.fp,
        }
        self._clean_permissions()  # Don't forget that !

    def tearDown(self):
        self.fp.close()

    def test_viewpoint_get_list_anonymous(self):
        with self.assertNumQueries(3):
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
        # List must still contain ALL viewpoints even those with no
        # pictures and pictures with other states than ACCEPTED
        self.assertEqual(3, data.get('count'))

    def test_anonymous_access_without_accepted_picture(self):
        # User is not authenticated yet
        response = self.client.get(
            reverse(
                'tropp:viewpoint-detail',
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
                'tropp:viewpoint-detail',
                args=[self.viewpoint_without_picture.pk],
            )
        )
        self.assertEqual(status.HTTP_200_OK, response.status_code)

    def test_anonymous_options_request_returns_correct_search_filters(self):
        ViewpointFactory(properties={
            'commune': 'Rouperou-le-coquet',
            'themes': ['foo', 'Bar']
        })
        ViewpointFactory(properties={
            'commune': 'Montcuq',
            'themes': ['Bar']
        })
        data = self.client.get(
            reverse('tropp:viewpoint-filters')
        ).json()
        self.assertEqual(data.get('cities'), ['Montcuq', 'Rouperou-le-coquet'])
        self.assertEqual(data.get('themes'), ['Bar', 'foo'])

    def test_authenticated_options_request_returns_all_search_filters(self):
        self.client.force_authenticate(user=self.user)
        data = self.client.get(
            reverse('tropp:viewpoint-filters')
        ).json()
        self.assertIsNotNone(data.get('cities'))
        self.assertIsNotNone(data.get('themes'))

        # Even if we have 3 users, we only get those who have pictures
        self.assertEqual(3, get_user_model().objects.count())
        self.assertEqual(2, len(data.get('photographers')))

    def test_viewpoint_search_anonymous(self):
        # Simple viewpoint search feature
        data = self.client.get(
            reverse('tropp:viewpoint-list'),
            {'search': 'accepted'},
        ).json()
        self.assertEqual(data.get('count'), 1)

    def test_viewpoint_search_with_auth(self):
        # Simple viewpoint search feature with auth
        self.client.force_authenticate(user=self.user)
        data = self.client.get(
            reverse('tropp:viewpoint-list'),
            {'search': 'Basic'},
        ).json()
        self.assertEqual(data.get('count'), 1)

    def test_viewpoint_picture_filter_anonymous(self):
        data = self.client.get(
            reverse('tropp:viewpoint-list'),
            {'pictures__id': self.viewpoint_with_accepted_picture.pictures
                .first().pk},
        ).json()
        self.assertEqual(data.get('count'), 1)

    def test_viewpoint_picture_filter_with_auth(self):
        self.client.force_authenticate(user=self.user)
        data = self.client.get(
            reverse('tropp:viewpoint-list'),
            {'pictures__id': self.viewpoint_with_accepted_picture.pictures
                .first().pk},
        ).json()
        self.assertEqual(data.get('count'), 1)

    def test_viewpoint_photographer_filter_anonymous(self):
        picture = self.viewpoint_with_accepted_picture.pictures.first()
        data = self.client.get(
            reverse('tropp:viewpoint-list'),
            {'pictures__owner__uuid': picture.owner.uuid},
        ).json()
        self.assertEqual(data.get('count'), 1)

    def test_viewpoint_photographer_filter_with_auth(self):
        self.client.force_authenticate(user=self.user)
        picture = self.viewpoint_with_accepted_picture.pictures.first()
        data = self.client.get(
            reverse('tropp:viewpoint-list'),
            {'pictures__owner__uuid': picture.owner.uuid},
        ).json()
        self.assertEqual(data.get('count'), 1)

    def test_viewpoint_search_date(self):
        list_url = reverse('tropp:viewpoint-list')
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

    def test_viewpoint_search_json(self):
        list_url = reverse('tropp:viewpoint-list')
        ViewpointFactory(
            label="Viewpoint for search",
            pictures__state=STATES.ACCEPTED,
            properties={
                "commune": "Rouperou-le-coquet",
                "themes": ['foo', 'bar', 'baz'],
                "voie": "coin d'en bas de la rue du bout",
                "site": "Carrière des petits violoncelles",
            },
        )
        self.assertEqual(self.client.get(list_url).json()['count'], 2)
        data = self.client.get(
            list_url, {'properties__commune': 'Rouperou-le-coquet'}
        ).json()
        self.assertEqual(data.get('count'), 1)
        data = self.client.get(list_url, {'properties__voie': 'rue'}).json()
        self.assertEqual(data.get('count'), 1)
        data = self.client.get(
            list_url, {'properties__themes[]': ['foo']}
        ).json()
        self.assertEqual(data.get('count'), 1)
        data = self.client.get(
            list_url, {'properties__themes[]': ['bar', 'foo']}
        ).json()
        self.assertEqual(data.get('count'), 1)
        data = self.client.get(
            list_url, {'properties__themes[]': ['bar', 'foobar']}
        ).json()
        self.assertEqual(data.get('count'), 0)
        data = self.client.get(
            list_url, {'properties__site': 'carrière'}
        ).json()
        self.assertEqual(data.get('count'), 1)

    def _viewpoint_create(self):
        return self.client.post(
            reverse('tropp:viewpoint-list'),
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

    def _viewpoint_create_with_picture(self):
        return self.client.post(
            reverse('tropp:viewpoint-list'),
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
        self.assertIn('placeholder', Feature.objects.get(
            id=self.viewpoint_with_accepted_picture.point.id
        ).properties['viewpoint_picture'])

    def _viewpoint_delete(self):
        return self.client.delete(
            reverse('tropp:viewpoint-detail', args=[self.viewpoint.pk])
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

    def _viewpoint_update(self):
        return self.client.patch(
            reverse('tropp:viewpoint-detail', args=[
                self.viewpoint_with_accepted_picture.pk]),
            {
                'label': 'test',
                'properties': {'test_update': 'ok'},
                'point': {
                    "type": "Point",
                    "coordinates": [0.0, 1.0]
                }
            },
            format='json',
        )

    def test_viewpoint_update_anonymous(self):
        response = self._viewpoint_update()
        # User is not authenticated
        self.assertEqual(status.HTTP_401_UNAUTHORIZED, response.status_code)

    def test_viewpoint_update_with_auth(self):
        self.client.force_authenticate(user=self.user)
        response = self._viewpoint_update()
        # User is authenticated but doesn't have permission to update the
        # viewpoint.
        self.assertEqual(status.HTTP_403_FORBIDDEN, response.status_code)

    def test_viewpoint_update_with_auth_and_perms(self):
        self.client.force_authenticate(user=self.user)
        self._set_permissions(['change_viewpoint', ])

        response = self._viewpoint_update()

        # User is authenticated and have permission to update the viewpoint.
        self.assertEqual(status.HTTP_200_OK, response.status_code)

        # Check if the viewpoint is correctly updated
        viewpoint = Viewpoint.objects.get(
            pk=self.viewpoint_with_accepted_picture.pk
        )
        self.assertEqual(response.data['label'], viewpoint.label)
        self.assertEqual(
            response.data['properties']['test_update'],
            viewpoint.properties['test_update']
        )

        # Check if the viewpoint's feature is correctly updated by the signal
        feature = Feature.objects.get(
            pk=self.viewpoint_with_accepted_picture.point.pk
        )
        self.assertEqual(
            response.data['label'],
            feature.properties['viewpoint_label']
        )
        self.assertEqual(
            self.viewpoint_with_accepted_picture.pk,
            feature.properties['viewpoint_id']
        )
        self.assertEqual(
            response.data['geometry']['coordinates'],
            [feature.geom.coords[0], feature.geom.coords[1]]
        )

    def test_add_picture_on_viewpoint_with_auth_and_perms(self):
        self.client.force_authenticate(user=self.user)
        self._set_permissions(['change_viewpoint', ])

        # We add a more recent picture to the viewpoint
        date = timezone.datetime(2019, 1, 1, tzinfo=timezone.utc)
        file = SimpleUploadedFile(
            name='test.jpg',
            content=open(
                'terracommon/tropp/tests/placeholder.jpg',
                'rb',
            ).read(),
            content_type='image/jpeg',
        )
        response = self.client.patch(
            reverse('tropp:viewpoint-detail', args=[
                self.viewpoint_with_accepted_picture.pk]),
            {
                'picture.date': date,
                'picture.file': file
            },
            format='multipart',
        )
        self.assertEqual(status.HTTP_200_OK, response.status_code)

        viewpoint = Viewpoint.objects.get(
            pk=self.viewpoint_with_accepted_picture.pk
        )
        self.assertEqual(2, len(viewpoint.pictures.all()))
        self.assertIn(
            file.name.split('.')[0],
            viewpoint.pictures.latest().file.name
        )

        feature = Feature.objects.get(
            pk=self.viewpoint_with_accepted_picture.point.pk
        )
        # Check if the signal has been sent after patching
        self.assertIn(
            file.name.split('.')[0],
            feature.properties['viewpoint_picture']
        )

    def test_ordering_in_list_view(self):
        self.client.force_authenticate(user=self.user)
        data = self.client.get(
            reverse('tropp:viewpoint-list')
        ).json()
        # Now test that viewpoints are ordered in chronological order
        first_viewpoint = Viewpoint.objects.get(
            id=data.get('results')[0]['id']
        )
        second_viewpoint = Viewpoint.objects.get(
            id=data.get('results')[1]['id']
        )
        self.assertTrue(
            first_viewpoint.created_at > second_viewpoint.created_at
        )

    def test_list_viewset_return_distinct_objects(self):
        # We add a more recent picture to the viewpoint
        date = timezone.datetime(2019, 1, 1, tzinfo=timezone.utc)
        file = SimpleUploadedFile(
            name='test.jpg',
            content=open(
                'terracommon/tropp/tests/placeholder.jpg',
                'rb',
            ).read(),
            content_type='image/jpeg',
        )
        Picture.objects.create(
            viewpoint=self.viewpoint_with_accepted_picture,
            owner=self.user,
            date=date,
            file=file,
            state=STATES.ACCEPTED,
        )

        # Viewpoint should appears only once in the list
        data = self.client.get(
            reverse('tropp:viewpoint-list')
        ).json()
        self.assertEqual(1, data.get('count'))

    def test_pdf_view_must_return_pdf_when_authenticated(self):
        self.client.force_authenticate(user=self.user)
        data = self.client.get(
            reverse(
                'tropp:viewpoint-pdf',
                args=[self.viewpoint.pk],
            )
        )
        self.assertEqual(status.HTTP_200_OK, data.status_code)
        self.assertIn('application/pdf', data['Content-Type'])
