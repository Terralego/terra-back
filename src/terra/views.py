from rest_framework import viewsets

from .models import Layer
from .serializers import LayerSerializer


class LayerViewSet(viewsets.ModelViewSet):
    queryset = Layer.objects.all()
    serializer_class = LayerSerializer
