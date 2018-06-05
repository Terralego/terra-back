from django.conf import settings
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient

from terracommon.terra.tests.factories import TerraUserFactory
from terracommon.trrequests.models import UserRequest
from terracommon.trrequests.permissions import IsOwnerOrStaff

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

        self.user = TerraUserFactory(organizations=1)
        self.client.force_authenticate(user=self.user)
        self.organization = self.user.organizations.all()[0]

    def test_request_creation(self):
        request = {
            'state': 0,
            'properties': {
                'myproperty': 'myvalue',
            },
            'geojson': self.geojson,
            'organization': [self.organization.pk]

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

        self.assertEqual(request.state, 0)
        self.assertDictEqual(layer_geojson, request.layer.to_geojson())
        self.assertEqual(
            3,
            request.layer.features.all().count()
            )

        """Test listing requests with no can_read_self_requests permission"""
        response = self.client.get(reverse('request-list'))
        self.assertEqual(200, response.status_code)
        self.assertEqual(0, len(response.json()))

        response = self.client.get(
            reverse('request-detail', args=[request.pk]),)
        self.assertEqual(404, response.status_code)

        """And with the permission"""
        self._set_permissions(['can_read_self_requests', ])
        response = self.client.get(reverse('request-list'))
        self.assertEqual(200, response.status_code)
        self.assertEqual(self.user.userrequests.all().count(),
                         len(response.json()))

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
