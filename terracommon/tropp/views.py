from rest_framework import permissions, viewsets
from rest_framework.filters import SearchFilter
from url_filter.integrations.drf import DjangoFilterBackend

from .models import Campaign, Document, Picture, Theme, Viewpoint
from .serializers import (CampaignSerializer, DetailCampaignNestedSerializer,
                          DocumentSerializer, ListCampaignNestedSerializer,
                          PictureSerializer, ThemeSerializer,
                          ViewpointSerializer)


class ViewpointViewSet(viewsets.ModelViewSet):
    serializer_class = ViewpointSerializer
    permission_classes = [
        permissions.DjangoModelPermissionsOrAnonReadOnly,
    ]

    def get_queryset(self):
        if self.request.user.is_authenticated:
            return Viewpoint.objects.all()
        return Viewpoint.objects.with_accepted_pictures()


class CampaignViewSet(viewsets.ModelViewSet):
    queryset = Campaign.objects.all()
    permission_classes = [permissions.DjangoModelPermissions]
    http_method_names = ['get', 'post', 'put', 'delete', 'options']
    filter_backends = (SearchFilter, DjangoFilterBackend)
    search_fields = ('label', )
    filter_fields = ('created_at', )  # TODO add state see CallableFilter

    def get_queryset(self):
        # Filter only on assigned campaigns for photographs
        user = self.request.user
        if (self.action == 'list'
                and not user.has_perm('tropp.manage_all_campaigns')):
            return super().get_queryset().filter(assignee=user)
        return super().get_queryset()

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)

    def check_object_permissions(self, request, obj: Campaign):
        # Prevent acting on unassigned campaigns for photographs
        if (not request.user.has_perm('tropp.manage_all_campaigns')
                and obj.assignee != request.user):
            self.permission_denied(request)
        super().check_object_permissions(request, obj)

    def get_serializer_class(self):
        if self.action == 'list':
            return ListCampaignNestedSerializer
        if self.action == 'retrieve':
            return DetailCampaignNestedSerializer
        return CampaignSerializer


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
