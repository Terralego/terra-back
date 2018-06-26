from django.conf import settings
from django.core.exceptions import PermissionDenied
from django.db.models import Q
from django.http.response import HttpResponse, HttpResponseServerError
from django.shortcuts import get_object_or_404
from rest_framework import permissions, viewsets
from rest_framework.decorators import detail_route, list_route
from rest_framework.filters import SearchFilter
from rest_framework.response import Response

from terracommon.events.signals import event

from .models import Comment, UserRequest
from .serializers import (CommentSerializer, UploadFileSerializer,
                          UserRequestSerializer)


class RequestViewSet(viewsets.ModelViewSet):
    serializer_class = UserRequestSerializer
    permission_classes = [permissions.IsAuthenticated, ]
    filter_backends = (SearchFilter, )
    search_fields = ('properties', )

    def get_queryset(self):
        if self.request.user.has_perm('trrequests.can_read_all_requests'):
            return UserRequest.objects.all()
        elif self.request.user.has_perm('trrequests.can_read_self_requests'):
            return UserRequest.objects.filter(
                Q(owner=self.request.user)
                | Q(reviewers__in=[self.request.user, ])
                )
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


class UploadFileViewSet(viewsets.ModelViewSet):
    serializer_class = UploadFileSerializer
    permission_classes = [permissions.IsAuthenticated, ]

    def get_queryset(self, *args, **kwargs):
        comment_pk = self.kwargs.get('comment_pk')
        comment = get_object_or_404(Comment, pk=comment_pk)
        return comment.files.all()

    def create(self, request, *args, **kwargs):
        self.request.data['comment'] = self.kwargs.get('comment_pk')
        if request.FILES.get('file'):
            self.request.data['initial_filename'] = self.request.FILES.get(
                'file').name
        return super().create(request, *args, **kwargs)

    def patch(self, request, *args, **kwargs):
        self.request.data['comment'] = self.kwargs.get('comment_pk')
        if request.FILES.get('file'):
            self.request.data['initial_filename'] = self.request.FILES.get(
                'file').name
        return super().partial_update(request, *args, **kwargs)

    @detail_route(methods=['get'], url_path='download')
    def get_details(self, request, request_pk=None, comment_pk=None, pk=None):
        uf = self.get_object()
        filename = uf.initial_filename
        file_pointer = uf.file.open()
        response = HttpResponse(file_pointer,
                                content_type='application/octet-stream')
        response['Content-Disposition'] = f'attachment; filename={filename}'
        return response
