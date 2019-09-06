from django.conf import settings
from django.db.models import Q
from django.http.response import Http404, HttpResponseServerError
from django.shortcuts import get_object_or_404
from rest_framework import mixins, permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.filters import SearchFilter
from rest_framework.response import Response
from url_filter.integrations.drf import DjangoFilterBackend

from terracommon.accounts.permissions import TokenBasedPermission
from terracommon.core.filters import JSONFieldOrderingFilter
from terracommon.document_generator.helpers import get_media_response
from terracommon.events.signals import event

from .models import UserRequest
from .serializers import CommentSerializer, UserRequestSerializer


class RequestViewSet(viewsets.ModelViewSet):
    serializer_class = UserRequestSerializer
    permission_classes = [permissions.IsAuthenticated, ]
    filter_backends = (SearchFilter, JSONFieldOrderingFilter,
                       DjangoFilterBackend,)
    search_fields = ('id', 'properties', 'expiry')
    filter_fields = ('state', 'reviewers', 'expiry')

    def get_queryset(self):
        if self.request.user.has_perm('trrequests.can_read_all_requests'):

            # Return  all non-draft request
            # except for the one the user is the owner.
            return UserRequest.objects.exclude(
                ~Q(owner=self.request.user)
                & Q(state=settings.STATES.DRAFT)
            )
        elif self.request.user.has_perm('trrequests.can_read_self_requests'):
            return UserRequest.objects.filter(
                Q(owner=self.request.user)
                | Q(reviewers__in=[self.request.user, ])
            ).distinct()
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

    @action(detail=False, methods=['get'])
    def schema(self, request):
        if isinstance(settings.REQUEST_SCHEMA, dict):
            return Response(settings.REQUEST_SCHEMA)
        else:
            return HttpResponseServerError()

    @action(detail=True, methods=['get'])
    def read(self, request, pk):
        self.get_object().user_read(request.user)
        userrequest = UserRequestSerializer(
            self.get_object(),
            context={'request': self.request})

        return Response(
            userrequest.data,
            status=status.HTTP_200_OK)


class CommentViewSet(mixins.CreateModelMixin,
                     mixins.RetrieveModelMixin,
                     mixins.ListModelMixin,
                     viewsets.GenericViewSet):
    serializer_class = CommentSerializer
    permission_classes = [permissions.IsAuthenticated, ]

    def get_queryset(self, *args, **kwargs):
        request_pk = self.kwargs.get('request_pk')

        return get_object_or_404(
            UserRequest,
            pk=request_pk).get_comments_for_user(self.request.user)

    def perform_create(self, serializer):

        if 'is_internal' in serializer.validated_data:
            if (serializer.validated_data['is_internal'] is True
                    and not self.request.user.has_perm(
                        'trrequests.can_internal_comment_requests')):
                raise PermissionDenied(
                    'Permission missing to create internal comment')

            elif (serializer.validated_data['is_internal'] is False
                  and not self.request.user.has_perm(
                        'trrequests.can_comment_requests')):
                raise PermissionDenied(
                    'Permission missing to create public comment')

        auto_data = {
            'owner': self.request.user,
            'userrequest': get_object_or_404(UserRequest,
                                             pk=self.kwargs.get('request_pk'))
        }

        return serializer.save(**auto_data)

    @action(detail=True, methods=['get'], permission_classes=(TokenBasedPermission,))
    def attachment(self, request, request_pk=None, pk=None):
        comment = self.get_object()
        if not comment.attachment:
            raise Http404('Attachment does not exist')

        response = get_media_response(
            request, comment.attachment,
            headers={
                'Content-Disposition': (
                    'attachment;'
                    f' filename={comment.filename}'),
            }
        )

        return response
