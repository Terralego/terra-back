from collections import OrderedDict

import coreapi
import coreschema
from rest_framework import permissions, viewsets
from rest_framework.filters import SearchFilter
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework.views import APIView

from ..core.filters import DateFilterBackend, SchemaAwareDjangoFilterBackend
from .filters import CampaignFilterBackend
from .serializers import *


class RestPageNumberPagination(PageNumberPagination):
    page_size_query_param = 'page_size'

    def get_paginated_response(self, data):
        page = self.page

        next_page = page.next_page_number() if page.has_next() else None
        previous_page = (page.previous_page_number() if page.has_previous()
                         else None)

        return Response(OrderedDict([
            ('count', page.paginator.count),
            ('num_pages', page.paginator.num_pages),
            ('next', next_page),
            ('previous', previous_page),
            ('page_size', self.get_page_size(self.request)),
            ('results', data),
        ]))


class ViewpointViewSet(viewsets.ModelViewSet):
    serializer_class = ViewpointSerializerWithPicture
    permission_classes = [
        permissions.DjangoModelPermissionsOrAnonReadOnly,
    ]
    filter_backends = (
        SearchFilter,
        SchemaAwareDjangoFilterBackend,
        DateFilterBackend,
    )
    filter_fields_schema = [
        coreapi.Field(
            name='pictures__id',
            required=False,
            location='query',
            schema=coreschema.Integer(
                title="Picture id",
                description="Picture id to filter on",
            ),
        ),
        coreapi.Field(
            name='pictures__owner__id',
            required=False,
            location='query',
            schema=coreschema.Integer(
                title="Photographer id",
                description="Photographer id to filter on",
            ),
        ),
    ]
    filter_fields = ['pictures']
    search_fields = ('id', )
    date_search_field = 'pictures__date__date'
    pagination_class = RestPageNumberPagination

    def get_queryset(self):
        if self.request.user.is_authenticated:
            return Viewpoint.objects.all()
        return Viewpoint.objects.with_accepted_pictures()

    def get_serializer_class(self):
        if self.action == 'list':
            return SimpleViewpointSerializer
        return ViewpointSerializerWithPicture


class ViewpointAdvancedSearchOptions(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, format=None):
        viewpoint_labels = ViewpointLabelSerializer(
            Viewpoint.objects.all(), many=True
        ).data
        photographers = PhotographerLabelSerializer(
            get_user_model().objects.all(), many=True
        ).data
        return Response({
            'viewpoints': viewpoint_labels,
            'photographers': photographers,
        })


class CampaignViewSet(viewsets.ModelViewSet):
    queryset = Campaign.objects.all()
    permission_classes = [permissions.DjangoModelPermissions]
    http_method_names = ['get', 'post', 'put', 'delete', 'options']
    filter_backends = (CampaignFilterBackend, DateFilterBackend, SearchFilter)
    date_search_field = 'created_at'
    search_fields = ('label', )
    pagination_class = RestPageNumberPagination

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
    pagination_class = RestPageNumberPagination

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)


class DocumentViewSet(viewsets.ModelViewSet):
    queryset = Document.objects.all()
    serializer_class = DocumentSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = RestPageNumberPagination

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)
