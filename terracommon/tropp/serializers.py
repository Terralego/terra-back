from django.contrib.auth import get_user_model
from rest_framework import serializers
from rest_framework_gis.fields import GeometryField
from versatileimagefield.serializers import VersatileImageFieldSerializer

from .models import Campaign, Document, Picture, Theme, Viewpoint

UserModel = get_user_model()


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


class SimplePictureSerializer(PictureSerializer):
    class Meta:
        model = Picture
        fields = ('date', 'file', 'owner', )


class ViewpointSerializer(serializers.ModelSerializer):
    class Meta:
        model = Viewpoint
        fields = '__all__'


class ViewpointSerializerWithPicture(ViewpointSerializer):
    picture = SimplePictureSerializer(required=False)

    class Meta:
        model = Viewpoint
        fields = ('label', 'point', 'properties', 'picture', )

    def create(self, validated_data):
        if 'picture' in validated_data:
            return self.create_with_picture(validated_data)
        return Viewpoint.objects.create(**validated_data)

    def create_with_picture(self, validated_data):
        picture_data = validated_data.pop('picture')
        viewpoint = Viewpoint.objects.create(**validated_data)
        Picture.objects.create(
            viewpoint=viewpoint,
            owner=self.context['request'].user,
            **picture_data,
        )
        return viewpoint


class DocumentSerializer(serializers.ModelSerializer):
    owner = serializers.ReadOnlyField(source='owner.email')

    class Meta:
        model = Document
        fields = '__all__'


class ThemeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Theme
        fields = '__all__'
