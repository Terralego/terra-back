from rest_framework import viewsets
from rest_framework.renderers import JSONRenderer
from rest_framework.response import Response

from terracommon.core.renderers import CSVRenderer

from .models import DataStore
from .permissions import IsAuthenticatedAndDataStoreAllowed
from .serializers import DataStoreSerializer


class DataStoreViewSet(viewsets.ModelViewSet):
    renderer_classes = (JSONRenderer, CSVRenderer, )

    permission_classes = (IsAuthenticatedAndDataStoreAllowed, )
    serializer_class = DataStoreSerializer
    lookup_field = 'key'
    lookup_value_regex = '[^/]+'

    def get_queryset(self):
        return DataStore.objects.get_datastores_for_user(self.request.user)

    def update(self, request, key=None):
        obj = self.get_object()

        serializer = self.get_serializer(obj, data=request.data)

        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(serializer.data)
