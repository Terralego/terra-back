from django.contrib.auth import get_user_model
from rest_framework import permissions, viewsets
from rest_framework.filters import SearchFilter
from rest_framework.response import Response
from rest_framework.views import APIView
from url_filter.integrations.drf import DjangoFilterBackend

from .models import Campaign, Document, Picture, Theme, Viewpoint
from .serializers import (CampaignSerializer, DetailCampaignNestedSerializer,
                          DocumentSerializer, ListCampaignNestedSerializer,
                          PhotographerLabelSerializer, PictureSerializer,
                          ThemeLabelSerializer, ThemeSerializer,
                          ViewpointLabelSerializer,
                          ViewpointSerializerWithPicture)


class ViewpointViewSet(viewsets.ModelViewSet):
    serializer_class = ViewpointSerializerWithPicture
    permission_classes = [
        permissions.DjangoModelPermissionsOrAnonReadOnly,
    ]
    filter_backends = (SearchFilter, DjangoFilterBackend, )
    search_fields = ('label', )

    def get_queryset(self):
        if self.request.user.is_authenticated:
            return Viewpoint.objects.all()
        return Viewpoint.objects.with_accepted_pictures()


class ViewpointAdvancedSearchOptions(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, format=None):
        viewpoint_labels = ViewpointLabelSerializer(
            Viewpoint.objects.all(), many=True
        ).data
        theme_labels = ThemeLabelSerializer(
            Theme.objects.all(), many=True
        ).data
        photographers = PhotographerLabelSerializer(
            get_user_model().objects.all(), many=True
        ).data
        return Response({
            'viewpoints': viewpoint_labels,
            'themes': theme_labels,
            'photographers': photographers,
        })


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
