from django.test import TestCase
from rest_framework import generics
from rest_framework.settings import api_settings
from rest_framework.test import APIRequestFactory

from terracommon.core.filters import JSONFieldOrderingFilter
from terracommon.terra.models import Layer
from terracommon.terra.serializers import LayerSerializer

factory = APIRequestFactory()


class JSONOrderingTestCache(TestCase):

    def setUp(self):
        for idx in range(3):
            data = {
                'name': 'a' * (idx + 1),
                'schema': {
                    'key': idx,
                }
            }
            # using Layer model as fake tests models needs lot of development
            Layer.objects.create(**data)

    def test_json_ordering(self):
        class OrderingListView(generics.ListAPIView):
            permission_classes = ()
            queryset = Layer.objects.all()
            serializer_class = LayerSerializer
            filter_backends = (JSONFieldOrderingFilter, )
            ordering = ['name', ]
            ordering_fields = ['schema', ]

        view = OrderingListView.as_view()

        # testing ascending
        request = factory.get('/',
                              {api_settings.ORDERING_PARAM: 'schema__key'})
        response = view(request)

        self.assertListEqual(
            [0, 1, 2],
            [i['schema']['key'] for i in response.data['results']])

        # testing descending
        request = factory.get('/',
                              {api_settings.ORDERING_PARAM: '-schema__key'})
        response = view(request)

        self.assertListEqual(
            [2, 1, 0],
            [i['schema']['key'] for i in response.data['results']])

        request = factory.get('/', {api_settings.ORDERING_PARAM: 'name'})
        response = view(request)

        # testing normal field
        self.assertListEqual(
            [0, 1, 2],
            [i['schema']['key'] for i in response.data['results']])
