from django.contrib.auth import get_user_model
from rest_framework import serializers
from rest_framework_gis.fields import GeometryField
from versatileimagefield.serializers import VersatileImageFieldSerializer

from .models import Campaign, Document, Picture, Theme, Viewpoint

UserModel = get_user_model()


class ViewpointSerializer(serializers.ModelSerializer):
    class Meta:
        model = Viewpoint
        fields = '__all__'


class PermissiveImageFieldSerializer(VersatileImageFieldSerializer):
    def get_attribute(self, instance):
        try:
            return super().get_attribute(instance)
        except AttributeError:
            return None


class SimpleViewpointSerializer(serializers.ModelSerializer):
    photo = PermissiveImageFieldSerializer(
        'tropp',
        source='pictures.first.file',
    )
    latlon = GeometryField(source='point.geom', read_only=True)

    class Meta:
        model = Viewpoint
        fields = ('pk', 'label', 'photo', 'latlon', 'status')
        geo_field = 'latlon'


class CampaignSerializer(serializers.ModelSerializer):
    owner = serializers.ReadOnlyField(source='owner.email')

    class Meta:
        model = Campaign
        fields = '__all__'


class DetailCampaignNestedSerializer(serializers.ModelSerializer):
    owner = serializers.ReadOnlyField(source='owner.email')
    viewpoints = SimpleViewpointSerializer(many=True, read_only=True)

    class Meta(CampaignSerializer.Meta):
        model = Campaign
        fields = '__all__'


class ListCampaignNestedSerializer(CampaignSerializer):
    photo = PermissiveImageFieldSerializer(
        'tropp',
        source='viewpoints.first.pictures.first.file',
    )

    class Meta(CampaignSerializer.Meta):
        model = Campaign
        fields = ('label', 'assignee', 'photo', 'status')


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
