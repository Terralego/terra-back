import operator
from collections import OrderedDict
from functools import reduce

import coreapi
import coreschema
from django.contrib.postgres.fields.jsonb import KeyTransform
from rest_framework import permissions, viewsets
from rest_framework.filters import SearchFilter
from rest_framework.generics import RetrieveAPIView
from rest_framework.metadata import BaseMetadata
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response

from ..core.filters import DateFilterBackend, SchemaAwareDjangoFilterBackend
from ..core.renderers import PdfRenderer
from .filters import CampaignFilterBackend
from .serializers import *


class ViewpointPdf(RetrieveAPIView):
    """
    Return a pdf representation of the given viewpoint by its id.
    """
    queryset = Viewpoint.objects.all()
    template_name = 'tropp/viewpoint_pdf.html'
    renderer_classes = (PdfRenderer,)
    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request, *args, **kwargs):
        properties_set = settings.TROPP_VIEWPOINT_PROPERTIES_SET['pdf']
        return Response({
            'viewpoint': self.get_object(),
            'properties_set': properties_set,
        })


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


class ViewpointFilters(BaseMetadata):
    @staticmethod
    def get_anonymous_search_filters():
        filter_values = {}
        searchable_properties = settings.TROPP_SEARCHABLE_PROPERTIES
        for key, field in searchable_properties.items():
            data = None
            transform = KeyTransform(field['json_key'], 'properties')
            queryset = (Viewpoint.objects
                        .annotate(**{key: transform})
                        .exclude(**{f"{key}__isnull": True})
                        .values_list(key, flat=True))
            if field['type'] == 'single':
                # Dedupe and sort with SQL
                data = queryset.order_by(key).distinct(key)
            elif field['type'] == 'many':
                # Dedupe and sort programmatically
                data = list(queryset)
                if data:
                    data = set(reduce(operator.concat, data))
                    data = sorted(data, key=str.lower)
            if data is not None:
                filter_values[key] = data
        return filter_values

    @staticmethod
    def get_authenticated_search_filters():
        viewpoints = ViewpointLabelSerializer(
            Viewpoint.objects.values('id', 'label'),
            many=True,
        ).data
        photographers = PhotographerLabelSerializer(
            get_user_model().objects.values('id', 'email'),
            many=True,
        ).data
        return {
            'viewpoints': viewpoints,
            'photographers': photographers
        }

    def determine_metadata(self, request, view):
        metadata = self.get_anonymous_search_filters()
        if request.user.is_authenticated:
            metadata.update(self.get_authenticated_search_filters())
        return metadata


class ViewpointViewSet(viewsets.ModelViewSet):
    metadata_class = ViewpointFilters
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

    def filter_queryset(self, queryset):
        # We must reorder the queryset here because initial filtering in
        # viewpoint model is not done right see
        # https://github.com/encode/django-rest-framework/issues/1717
        return super().filter_queryset(queryset).order_by('-created_at')

    def get_queryset(self):
        qs = Viewpoint.objects
        if self.request.user.is_authenticated:
            qs = qs.all().distinct()
        else:
            qs = qs.with_accepted_pictures()
        return qs.select_related('point').prefetch_related('pictures')

    def get_serializer_class(self):
        if self.action == 'list':
            if self.request.user.is_anonymous:
                return SimpleViewpointSerializer
            return SimpleAuthenticatedViewpointSerializer
        return ViewpointSerializerWithPicture


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
            if self.request.user.is_anonymous:
                return DetailCampaignNestedSerializer
            return DetailAuthenticatedCampaignNestedSerializer
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
