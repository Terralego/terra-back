import json

from django.test import TestCase

from rest_framework.test import APIClient
from rest_framework_json_api.utils import format_resource_type

from .models import Layer, Feature


class SchemaValidationTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.layer = Layer.objects.create(
            name="tree",
            schema={
                "name": {
                    "type": "string"
                },
                "age": {
                    "type": "integer"
                }
            })

    def test_feature_with_valid_properties_is_posted(self):
        """Feature with valid properties is successfully POSTed"""
        response = self.client.post('/api/layer/{}/feature/'.format(self.layer.id),
                                    json.dumps({"data": {
                                        "attributes": {
                                            "geom": "POINT(0 0)",
                                            "layer": self.layer.id,
                                            "name": "valid tree",
                                            "age": 10
                                        },
                                        "type": format_resource_type('Feature')}}),
                                    content_type='application/vnd.api+json'
                                    )

        features = Feature.objects.all()

        self.assertEqual(response.status_code, 201)
        self.assertEqual(len(features), 1)
        self.assertEqual(features[0].properties['name'], 'valid tree')

    def test_feature_with_missing_property_type_is_not_posted(self):
        """Feature with missing property type is not successfully POSTed"""
        response = self.client.post('/api/layer/{}/feature/'.format(self.layer.id),
                                    json.dumps({"data": {
                                        "attributes": {
                                            "geom": "POINT(0 0)",
                                            "layer": self.layer.id,
                                            "name": "invalid tree"
                                        },
                                        "type": format_resource_type('Feature')}}),
                                    content_type='application/vnd.api+json'
                                    )

        self.assertEqual(response.status_code, 400)
