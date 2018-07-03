from django.conf import settings
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient

from terracommon.accounts.tests.factories import TerraUserFactory
from terracommon.trrequests.models import UserRequest
from terracommon.trrequests.permissions import IsOwnerOrStaff
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
        response = self.client.post(reverse('request-list'),
                                    request,
                                    format='json')
        self.assertEqual(403, response.status_code)

        """Then we add the permissions to the user"""
        self._set_permissions(['can_create_requests', ])
        response = self.client.post(reverse('request-list'),
                                    request,
                                    format='json')

        self.assertEqual(201, response.status_code)

        request = UserRequest.objects.get(pk=response.data.get('id'))
        layer_geojson = response.data.get('geojson')

        self.assertEqual(request.state, settings.STATES.DRAFT)
        self.assertDictEqual(layer_geojson, request.layer.to_geojson())
        self.assertEqual(
            3,
            request.layer.features.all().count()
            )

        """Test listing requests with no can_read_self_requests permission"""
        response = self.client.get(reverse('request-list'))
        self.assertEqual(200, response.status_code)
        self.assertEqual(0, response.json().get('count'))

        response = self.client.get(
            reverse('request-detail', args=[request.pk]),)
        self.assertEqual(404, response.status_code)

        """And with the permission"""
        self._set_permissions(['can_read_self_requests', ])
        response = self.client.get(reverse('request-list'))
        self.assertEqual(200, response.status_code)
        self.assertEqual(self.user.userrequests.all().count(),
                         response.json().get('count'))

        """Check the detail view return also the same geojson data"""
        response = self.client.get(
            reverse('request-detail', args=[request.pk]),)

        self.assertEqual(200, response.status_code)
        layer_geojson = response.data.get('geojson')
        self.assertDictEqual(layer_geojson, request.layer.to_geojson())

        self._clean_permissions()

    def test_schema(self):
        response = self.client.get(reverse('request-schema'))
        self.assertDictEqual(settings.REQUEST_SCHEMA, response.json())

        settings.REQUEST_SCHEMA = None
        response = self.client.get(reverse('request-schema'))
        self.assertEqual(500, response.status_code)

    def test_object_permission(self):
        permission = IsOwnerOrStaff  # TODO
        dir(permission)

    def test_request_change_state(self):
        request = UserRequestFactory()
        new_state = 10
        self._set_permissions(['can_read_all_requests', ])

        """Test with the can_change_state_requests permission"""
        response = self.client.patch(
            reverse('request-detail', args=[request.pk]),
            {'state': new_state},
            format='json')

        self.assertEqual(200, response.status_code)
        request.refresh_from_db()
        self.assertEqual(new_state, request.state)

    def test_geojson_update(self):
        userrequest = UserRequestFactory(
            owner=self.user,
            layer__add_features=[{}, ])

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
