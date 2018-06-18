from django.conf import settings
from django.core.exceptions import PermissionDenied
from django.http import Http404
from django.http.response import HttpResponseServerError
from django.shortcuts import get_object_or_404
from rest_framework import permissions, viewsets
from rest_framework.decorators import detail_route, list_route
from rest_framework.response import Response
from rest_framework.status import HTTP_202_ACCEPTED

from .models import UserRequest
from .serializers import (CommentSerializer, OrganizationSerializer,
                          UserRequestSerializer)


class RequestViewSet(viewsets.ModelViewSet):
    serializer_class = UserRequestSerializer
    permission_classes = [permissions.IsAuthenticated, ]

    def get_queryset(self):
        if self.request.user.has_perm('trrequests.can_read_all_requests'):
            return UserRequest.objects.all()
        elif self.request.user.has_perm('trrequests.can_read_self_requests'):
            return self.request.user.userrequests.all()
        return UserRequest.objects.none()

    def create(self, request, *args, **kwargs):
        if not self.request.user.has_perm('trrequests.can_create_requests'):
            raise PermissionDenied

        if not self.request.user.has_perm(
                'trrequests.can_change_state_requests'):
            del self.request.data['state']

        return super().create(request, *args, **kwargs)

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)

    @list_route(methods=['get'], url_path='schema')
    def schema(self, request):
        if isinstance(settings.REQUEST_SCHEMA, dict):
            return Response(settings.REQUEST_SCHEMA)
        else:
            return HttpResponseServerError()

    @detail_route(methods=['post'], url_path='status')
    def status(self, request, pk):
        try:
            request = self.get_queryset().get(pk=pk)
        except self.get_queryset().model.DoesNotExist:
            raise Http404

        if (self.request.user.has_perm('trrequests.can_change_state_requests')
                and 'state' in self.request.data):
            request.state = int(self.request.data.get('state'))
            request.save()
            return Response(status=HTTP_202_ACCEPTED)
        raise PermissionDenied


class CommentViewSet(viewsets.ModelViewSet):
    serializer_class = CommentSerializer
    permission_classes = [permissions.IsAuthenticated, ]

    def get_queryset(self, *args, **kwargs):
        request_pk = self.kwargs.get('request_pk')
        if self.request.user.has_perm(
                'trrequests.can_internal_comment_requests'):
            request = get_object_or_404(UserRequest, pk=request_pk)
            return request.comments.all()
        elif self.request.user.has_perm('trrequests.can_comment_requests'):
            return self.request.user.userrequests.get(
                pk=request_pk).comments.filter(is_internal=False)
        return []

    def perform_create(self, serializer):
        if not (self.request.user.has_perm('trrequests.can_comment_requests')
                or self.request.user.has_perm(
                    'trrequests.can_internal_comment_requests')):
            raise PermissionDenied

        auto_datas = {
            'owner': self.request.user,
            'userrequest': get_object_or_404(UserRequest,
                                             pk=self.kwargs.get('request_pk'))
        }

        if not self.request.user.has_perm(
                'trrequests.can_internal_comment_requests'):
            auto_datas['is_internal'] = False

        serializer.save(**auto_datas)


class OrganizationViewSet(viewsets.ModelViewSet):
    serializer_class = OrganizationSerializer
    permission_classes = [permissions.IsAuthenticated, ]

    def get_queryset(self):
        return self.request.user.organizations.all()

    def perform_create(self, serializer):
        serializer.save(owner=[self.request.user, ])
