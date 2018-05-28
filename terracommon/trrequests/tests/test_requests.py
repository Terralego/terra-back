from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient

from terracommon.terra.models import Layer
from terracommon.terra.tests.factories import TerraUserFactory


class RequestTestCase(TestCase):
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
        response = self.client.post(
            reverse('request-list'),
            {
                'state': 0,
                'properties': {
                    'myproperty': 'myvalue',
                },
                'geojson': self.geojson,
                'organization': [self.organization.pk]

            }, format='json')

        self.assertEqual(201, response.status_code)

        layer_pk = response.data.get('layer').get('id', None)
        self.assertIsInstance(layer_pk, int)
        self.assertEqual(
            3,
            Layer.objects.get(pk=layer_pk).features.all().count()
            )
