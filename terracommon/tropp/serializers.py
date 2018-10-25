from django.contrib.auth import get_user_model
from rest_framework import serializers

from .models import Campaign, Document, ObservationPoint, Picture, Theme

UserModel = get_user_model()


class ObservationPointSerializer(serializers.ModelSerializer):
    class Meta:
        model = ObservationPoint
        fields = '__all__'


class CampaignSerializer(serializers.ModelSerializer):
    class Meta:
        model = Campaign
        fields = '__all__'


class PictureSerializer(serializers.ModelSerializer):
    owner = serializers.ReadOnlyField(source='owner.email')

    class Meta:
        model = Picture
        fields = '__all__'


class DocumentSerializer(serializers.ModelSerializer):
    owner = serializers.ReadOnlyField(source='owner.email')

    class Meta:
        model = Document
        fields = '__all__'


class ThemeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Theme
        fields = '__all__'
