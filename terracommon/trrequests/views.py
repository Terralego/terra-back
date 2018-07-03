from django.conf import settings
from django.core.exceptions import PermissionDenied
from django.http.response import HttpResponseServerError
from django.shortcuts import get_object_or_404
from rest_framework import permissions, viewsets
from rest_framework.decorators import list_route
from rest_framework.filters import SearchFilter
from rest_framework.response import Response

from terracommon.events.signals import event

from .models import UserRequest
from .serializers import CommentSerializer, UserRequestSerializer


class RequestViewSet(viewsets.ModelViewSet):
    serializer_class = UserRequestSerializer
    permission_classes = [permissions.IsAuthenticated, ]
    filter_backends = (SearchFilter, )
    search_fields = ('properties', )

    def get_queryset(self):
        if self.request.user.has_perm('trrequests.can_read_all_requests'):
            return UserRequest.objects.all()
        elif self.request.user.has_perm('trrequests.can_read_self_requests'):
            return self.request.user.userrequests.all()
        return UserRequest.objects.none()

    def create(self, request, *args, **kwargs):
        if not self.request.user.has_perm('trrequests.can_create_requests'):
            raise PermissionDenied

        return super().create(request, *args, **kwargs)

    def perform_create(self, serializer):
        instance = serializer.save(owner=self.request.user)
        event.send(
            self.__class__,
            action="USERREQUEST_CREATED",
            user=self.request.user,
            instance=instance)

    def patch(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs)

    @list_route(methods=['get'], url_path='schema')
    def schema(self, request):
        if isinstance(settings.REQUEST_SCHEMA, dict):
            return Response(settings.REQUEST_SCHEMA)
        else:
            return HttpResponseServerError()


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
