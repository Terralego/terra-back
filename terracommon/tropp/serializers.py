from django.contrib.auth import get_user_model
from rest_framework import serializers
from rest_framework_gis.fields import GeometryField
from versatileimagefield.serializers import VersatileImageFieldSerializer

from .models import Campaign, Document, Picture, Viewpoint

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
    # Override to expose typed data
    statistics = serializers.DictField(
        child=serializers.IntegerField(),
        read_only=True,
    )
    status = serializers.BooleanField(read_only=True)

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


class ViewpointSerializerWithPicture(ViewpointSerializer):
    picture = SimplePictureSerializer(required=False, write_only=True)
    pictures = SimplePictureSerializer(many=True, read_only=True)

    class Meta:
        model = Viewpoint
        fields = ('id', 'label', 'point', 'properties', 'picture', 'pictures')

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


class ViewpointLabelSerializer(serializers.ModelSerializer):
    class Meta:
        model = Viewpoint
        fields = ('id', 'label', )


class PhotographerLabelSerializer(serializers.ModelSerializer):
    class Meta:
        model = get_user_model()
        fields = ('id', 'email', )
