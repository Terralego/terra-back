from rest_framework import permissions, viewsets

from terracommon.terra.serializers import LayerSerializer

from .models import Campaign, Document, Layer, ObservationPoint, Picture, Theme
from .serializers import (CampaignSerializer, DocumentSerializer,
                          ObservationPointSerializer, PictureSerializer,
                          ThemeSerializer)


class ObservationPointViewSet(viewsets.ModelViewSet):
    queryset = ObservationPoint.objects.all()
    serializer_class = ObservationPointSerializer


class CampaignViewSet(viewsets.ModelViewSet):
    queryset = Campaign.objects.all()
    serializer_class = CampaignSerializer


class PictureViewSet(viewsets.ModelViewSet):
    queryset = Picture.objects.all()
    serializer_class = PictureSerializer
    permission_classes = [permissions.IsAuthenticated, ]

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)


class DocumentViewSet(viewsets.ModelViewSet):
    queryset = Document.objects.all()
    serializer_class = DocumentSerializer
    permission_classes = [permissions.IsAuthenticated, ]

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)


class ThemeViewSet(viewsets.ModelViewSet):
    queryset = Theme.objects.all()
    serializer_class = ThemeSerializer


class LayerViewSet(viewsets.ModelViewSet):
    queryset = Layer.objects.all()
    serializer_class = LayerSerializer
