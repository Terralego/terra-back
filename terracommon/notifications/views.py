from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .serializers import UserNotificationSerializer


class NotificationViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = UserNotificationSerializer

    def get_queryset(self, *args, **kwargs):
        return self.request.user.notifications.all()

    @action(detail=False, methods=['get'])
    def read_all(self, *args, **kwargs):
        self.request.user.notifications.read_all()
        return Response(status.HTTP_200_OK)
