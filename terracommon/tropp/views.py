from rest_framework import permissions, viewsets

from .models import Campaign, Document, Viewpoint, Picture, Theme
from .serializers import (CampaignSerializer, DocumentSerializer,
                          ViewpointSerializer, PictureSerializer,
                          ThemeSerializer)


class ViewpointViewSet(viewsets.ModelViewSet):
    queryset = Viewpoint.objects.all()
    serializer_class = ViewpointSerializer
    permission_classes = [
        permissions.DjangoModelPermissionsOrAnonReadOnly,
    ]


class CampaignViewSet(viewsets.ModelViewSet):
    queryset = Campaign.objects.all()
    serializer_class = CampaignSerializer
    permission_classes = [permissions.DjangoModelPermissions,]


class PictureViewSet(viewsets.ModelViewSet):
    queryset = Picture.objects.all()
    serializer_class = PictureSerializer
    permission_classes = [permissions.DjangoModelPermissions]

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)


class DocumentViewSet(viewsets.ModelViewSet):
    queryset = Document.objects.all()
    serializer_class = DocumentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)


class ThemeViewSet(viewsets.ModelViewSet):
    queryset = Theme.objects.all()
    serializer_class = ThemeSerializer
