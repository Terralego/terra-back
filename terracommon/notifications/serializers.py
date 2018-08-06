from rest_framework import serializers

from .models import UserNotifications


class UserNotificationSerializer(serializers.ModelSerializer):

    class Meta:
        model = UserNotifications
        exclude = ('user', )
