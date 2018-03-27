import json

from django.conf import settings
from django.http.response import HttpResponseServerError

from rest_framework import viewsets, permissions
from rest_framework.decorators import detail_route, list_route
from rest_framework.response import Response

from .models import Request
from .permissions import IsOwnerOrStaff
from .serializers import RequestSerializer


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
            return Response(json.dumps(settings,REQUEST_SCHEMA))
        else:
            return HttpResponseServerError()

    @detail_route(url_path='comments')
    def comments(self, request, pk=None):
        feature = self.get_object()
        comments = feature.comments.order_by('-updated_at')
        return [comment for comment in comments]
