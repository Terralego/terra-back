import json

from django.conf import settings
from django.http.response import HttpResponseServerError
from django.shortcuts import get_object_or_404

from rest_framework import viewsets, permissions
from rest_framework.decorators import detail_route, list_route
from rest_framework.response import Response

from .permissions import IsOwnerOrStaff
from .serializers import RequestSerializer, OrganizationSerializer, \
    CommentSerializer
from .models import Request


class RequestViewSet(viewsets.ModelViewSet):
    serializer_class = RequestSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrStaff, ]

    def get_queryset(self):
        return self.request.user.requests.all()

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)

    @list_route(methods=['get'], url_path='schema')
    def schema(self, request):
        if settings.REQUEST_SCHEMA:
            return Response(json.dumps(settings.REQUEST_SCHEMA))
        else:
            return HttpResponseServerError()


class CommentViewSet(viewsets.ModelViewSet):
    serializer_class = CommentSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrStaff, ]

    def get_queryset(self, *args, **kwargs):
        request = get_object_or_404(Request, pk=self.kwargs.get('request_pk'))
        return request.comments.all()

    def perform_create(self, serializer):
        auto_datas = {
            'owner': self.request.user,
            'request': get_object_or_404(Request,
                                         pk=self.kwargs.get('request_pk'))
        }
        serializer.save(**auto_datas)



class OrganizationViewSet(viewsets.ModelViewSet):
    serializer_class = OrganizationSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrStaff, ]

    def get_queryset(self):
        return self.request.user.organizations.all()

    def perform_create(self, serializer):
        serializer.save(owner=[self.request.user, ])
