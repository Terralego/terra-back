import base64
import os
from unittest.mock import MagicMock

import magic
from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.core.files import File
from django.shortcuts import resolve_url
from django.test import TestCase
from django.urls import reverse
from geostore.tests.factories import LayerFactory
from rest_framework import status
from rest_framework.test import APIClient
from terra_accounts.tests.factories import TerraUserFactory
from terra_utils.settings import STATES

from terracommon.datastore.models import RelatedDocument
from terracommon.events.signals import event
from terracommon.trrequests.models import UserRequest
from terracommon.trrequests.serializers import UserRequestSerializer

from .factories import UserRequestFactory
from .mixins import TestPermissionsMixin


class RequestTestCase(TestCase, TestPermissionsMixin):
    geojson = {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "properties": {},
                "geometry": {
                    "type": "LineString",
                    "coordinates": [
                        [
                            2.30712890625,
                            48.83579746243093
                        ],
                        [
                            1.42822265625,
                            43.628123412124616
                        ]
                    ]
                }
            },
            {
                "type": "Feature",
                "properties": {},
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [
                        [
                            [
                                -1.549072265625,
                                43.49676775343911
                            ],
                            [
                                -2.340087890625,
                                43.25320494908846
                            ],
                            [
                                3.2244873046875,
                                42.07783959017503
                            ],
                            [
                                3.021240234375,
                                42.577354839557856
                            ],
                            [
                                -1.549072265625,
                                43.49676775343911
                            ]
                        ]
                    ]
                }
            },
            {
                "type": "Feature",
                "properties": {},
                "geometry": {
                    "type": "Point",
                    "coordinates": [
                        1.42822265625,
                        43.57641143300888
                    ]
                }
            }
        ]
    }

    def setUp(self):
        self.client = APIClient()

        self.user = TerraUserFactory()
        self.client.force_authenticate(user=self.user)

    def test_request_creation(self):
        request = {
            'properties': {
                'myproperty': 'myvalue',
            },
            'geojson': self.geojson,
        }
        """First we try with no rights"""
        response = self.client.post(reverse('trrequests:request-list'),
                                    request,
                                    format='json')
        self.assertEqual(403, response.status_code)

        """Then we add the permissions to the user"""
        self._set_permissions(['can_create_requests', ])
        response = self.client.post(reverse('trrequests:request-list'),
                                    request,
                                    format='json')

        self.assertEqual(201, response.status_code)

        request = UserRequest.objects.get(pk=response.data.get('id'))
        layer_geojson = response.data.get('geojson')

        self.assertEqual(request.state, STATES.DRAFT)
        self.assertDictEqual(layer_geojson, request.layer.to_geojson())
        self.assertEqual(
            3,
            request.layer.features.all().count()
            )

        """Test listing requests with no can_read_self_requests permission"""
        response = self.client.get(reverse('trrequests:request-list'))
        self.assertEqual(200, response.status_code)
        self.assertEqual(0, response.json().get('count'))

        response = self.client.get(
            reverse('trrequests:request-detail', args=[request.pk]),)
        self.assertEqual(404, response.status_code)

        """And with the permission"""
        self._set_permissions(['can_read_self_requests', ])
        response = self.client.get(reverse('trrequests:request-list'))
        self.assertEqual(200, response.status_code)
        self.assertEqual(self.user.userrequests.all().count(),
                         response.json().get('count'))

        request_to_review = UserRequestFactory()
        request_to_review.reviewers.add(self.user)
        response = self.client.get(reverse('trrequests:request-list'))
        self.assertEqual(200, response.status_code)
        self.assertEqual(self.user.userrequests.all().count() + 1,
                         response.json().get('count'))

        """Check the detail view return also the same geojson data"""
        response = self.client.get(
            reverse('trrequests:request-detail', args=[request.pk]),)

        self.assertEqual(200, response.status_code)
        layer_geojson = response.data.get('geojson')
        self.assertDictEqual(layer_geojson, request.layer.to_geojson())

        self._clean_permissions()

    def test_results_must_not_duplicate(self):
        self._set_permissions(['can_read_self_requests', ])
        request_to_review = UserRequestFactory(owner=self.user)
        request_to_review.reviewers.add(TerraUserFactory())
        request_to_review.reviewers.add(TerraUserFactory())

        response = self.client.get(reverse('trrequests:request-list'))
        self.assertEqual(self.user.userrequests.all().count(),
                         response.json().get('count'))
        self._clean_permissions()

    def test_schema(self):
        response = self.client.get(reverse('trrequests:request-schema'))
        self.assertDictEqual(settings.REQUEST_SCHEMA, response.json())

        settings.REQUEST_SCHEMA = None
        response = self.client.get(reverse('trrequests:request-schema'))
        self.assertEqual(500, response.status_code)

    def test_request_change_state(self):
        request = UserRequestFactory()
        new_state = 10
        self._set_permissions(['can_read_all_requests', ])

        handler = MagicMock()
        event.connect(handler)
        # Test with the can_change_state_requests permission
        # and tests event associated
        response = self.client.patch(
            reverse('trrequests:request-detail', args=[request.pk]),
            {'state': new_state},
            format='json')

        handler.assert_called_once_with(
            signal=event,
            action="USERREQUEST_STATE_CHANGED",
            sender=UserRequestSerializer,
            user=self.user,
            instance=request,
            old_state=request.state)

        self.assertEqual(200, response.status_code)
        request.refresh_from_db()
        self.assertEqual(new_state, request.state)

    def test_geojson_update(self):
        userrequest = UserRequestFactory(
            owner=self.user,
            layer__add_features=1)

        self.assertEqual(1, userrequest.layer.features.all().count())

        serializer = UserRequestSerializer()
        validated_data = {
            'layer': self.geojson,
        }
        serializer.update(userrequest, validated_data)
        userrequest.refresh_from_db()
        self.assertEqual(
            len(self.geojson['features']),
            userrequest.layer.features.all().count()
            )

    def test_userrequest_patched(self):
        self._set_permissions(['can_read_self_requests', ])

        old_properties = {'property': ''}
        userrequest = UserRequest.objects.create(owner=self.user,
                                                 layer=LayerFactory(),
                                                 properties=old_properties)

        receiver_callback = MagicMock()
        event.connect(receiver_callback)
        response = self.client.patch(reverse('trrequests:request-detail',
                                             kwargs={'pk': userrequest.pk}),
                                     {'properties': {'property': 'value'}},
                                     format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        receiver_callback.assert_called_with(
            sender=UserRequestSerializer,
            signal=event,
            action='USERREQUEST_PROPERTIES_CHANGED',
            user=self.user,
            instance=userrequest,
            old_properties=old_properties
        )
        event.disconnect(receiver_callback)
        self._clean_permissions()

    def test_upload_document(self):
        self._set_permissions(['can_create_requests', ])
        request = {
            'properties': {
                'myproperty': 'myvalue',
            },
            'geojson': self.geojson,
            'documents': [{
                'key': 'my_document',
                'document': ('data:image/png;base64,aGVsbG8gd29ybGQ=')
            }, ]
        }

        # First we try with no rights
        response = self.client.post(reverse('trrequests:request-list'),
                                    request,
                                    format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(UserRequest.objects
                                   .filter(documents__key='my_document')
                                   .exists())
        self._clean_permissions()

    def test_update_userrequest_with_wrong_document_format(self):
        layer = LayerFactory()
        userrequest = UserRequest.objects.create(
            owner=self.user,
            layer=layer,
            properties={},
        )

        self._set_permissions(['can_read_self_requests', ])
        response = self.client.put(
            resolve_url('trrequests:request-detail', pk=userrequest.pk),
            {
                'properties': {'noupdate': 'tada'},
                'geojson': {},
                'documents': [{
                    "key": "activity-0",
                    "document": ("documents/trrequests_userrequest/"
                                 f"{userrequest.pk}/activity-0")
                }],
            }
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self._clean_permissions()

        self.assertFalse(UserRequest.objects
                                    .filter(properties__noupdate='tada')
                                    .exists())
        self.assertFalse(UserRequest.objects
                                    .filter(documents__key="activity-0")
                                    .exists())

    def test_returned_document_are_base64(self):
        layer = LayerFactory()
        userrequest = UserRequest.objects.create(
            owner=self.user,
            layer=layer,
            properties={},
        )

        img = os.path.join(os.path.dirname(__file__), 'files', 'img.png')
        with open(img, 'rb') as f:
            self._set_permissions([
                'can_read_self_requests',
                'can_create_requests',
            ])
            document = (f'data:image/png;base64,'
                        f'{(base64.b64encode(f.read())).decode("utf-8")}')
            response = self.client.patch(
                resolve_url('trrequests:request-detail', pk=userrequest.pk),
                {
                    'geojson': self.geojson,
                    'documents': [{
                        'key': 'doctest',
                        'document': document,
                    }],
                }
            )
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            json_response = response.json()
            self.assertEqual(
                document,
                json_response['documents'][0]['document']
            )
            self._clean_permissions()

    def test_retrieve_related_document(self):
        layer = LayerFactory()
        userrequest = UserRequest.objects.create(
            owner=self.user,
            layer=layer,
            properties={},
        )
        img = os.path.join(os.path.dirname(__file__), 'files', 'img.png')
        with open(img, 'rb') as f:
            RelatedDocument.objects.create(
                key='document_to_test',
                object_id=userrequest.pk,
                content_type=ContentType.objects.get_for_model(userrequest.__class__),
                document=File(f)
            )

        self._set_permissions([
            'can_read_self_requests',
            'can_create_requests',
        ])
        response = self.client.get(
            resolve_url('trrequests:request-detail', pk=userrequest.pk),
        )
        self.assertEqual(status.HTTP_200_OK, response.status_code)
        json_reponse = response.json()
        self.assertIn(
            f'data:{magic.from_file(img, mime=True)};base64,',
            json_reponse['documents'][0]['document']
        )
        self._clean_permissions()
