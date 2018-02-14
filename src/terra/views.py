from rest_framework import viewsets

from .models import Layer, Feature
from .serializers import LayerSerializer, FeatureSerializer


class LayerViewSet(viewsets.ModelViewSet):
    queryset = Layer.objects.all()
    serializer_class = LayerSerializer


class FeatureViewSet(viewsets.ModelViewSet):
    queryset = Feature.objects.all()
    serializer_class = FeatureSerializer
