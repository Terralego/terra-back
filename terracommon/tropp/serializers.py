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
    geometry = GeometryField(source='point.geom', read_only=True)

    class Meta:
        model = Viewpoint
        fields = ('id', 'label', 'photo', 'geometry', 'status')


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
        fields = ('label', 'assignee', 'photo', 'statistics', 'status')


class PictureSerializer(serializers.ModelSerializer):
    owner = serializers.ReadOnlyField(source='owner.email')

    class Meta:
        model = Picture
        fields = '__all__'


class SimplePictureSerializer(PictureSerializer):
    class Meta:
        model = Picture
        fields = ('id', 'date', 'file', 'owner', )


class ViewpointSerializer(serializers.ModelSerializer):
    class Meta:
        model = Viewpoint
        fields = '__all__'


class ThemeLabelSerializer(serializers.ModelSerializer):
    class Meta:
        model = Theme
        fields = ('id', 'label', )


class ViewpointSerializerWithPicture(ViewpointSerializer):
    picture = SimplePictureSerializer(required=False, write_only=True)
    pictures = SimplePictureSerializer(many=True, read_only=True)
    themes = ThemeLabelSerializer(many=True, read_only=True)
    themes_ids = serializers.PrimaryKeyRelatedField(
        queryset=Theme.objects.all(),
        source='themes',
        write_only=True,
        required=False,
        many=True,
    )

    class Meta:
        model = Viewpoint
        fields = ('id', 'label', 'point', 'properties', 'themes',
                  'themes_ids', 'picture', 'pictures')

    def create(self, validated_data):
        picture_data = validated_data.pop('picture', None)
        viewpoint = super().create(validated_data)
        if picture_data is not None:
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


class ViewpointLabelSerializer(serializers.ModelSerializer):
    class Meta:
        model = Viewpoint
        fields = ('id', 'label', )


class PhotographerLabelSerializer(serializers.ModelSerializer):
    class Meta:
        model = get_user_model()
        fields = ('id', 'email', )
