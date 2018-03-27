from django.conf import settings

from rest_framework import serializers

from .models import Request


class RequestSerializer(serializers.ModelSerializer):

    class Meta:
        model = Request
        exclude = ('owner', )
