from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.exceptions import ObjectDoesNotExist
from rest_framework import serializers
from rest_framework.fields import SerializerMethodField
from rest_framework_gis.fields import GeometryField
from versatileimagefield.serializers import VersatileImageFieldSerializer

from terracommon.accounts.serializers import UserProfileSerializer
from terracommon.datastore.serializers import RelatedDocumentFileSerializer
from terracommon.terra.models import Feature, Layer

from .models import Campaign, Picture, Viewpoint

UserModel = get_user_model()


class PermissiveImageFieldSerializer(VersatileImageFieldSerializer):
    def get_attribute(self, instance):
        try:
            return super().get_attribute(instance)
        except (AttributeError, ObjectDoesNotExist):
            # Will silence any NoneType or failing query on attribute
            return None


class SimpleViewpointSerializer(serializers.ModelSerializer):
    picture = SerializerMethodField()
    point = GeometryField(source='point.geom')

    class Meta:
        model = Viewpoint
        fields = ('id', 'label', 'picture', 'point')

    def get_picture(self, viewpoint):
        try:
            return VersatileImageFieldSerializer('tropp').to_native(
                viewpoint.ordered_pics[0].file
            )
        except IndexError:
            return None


class SimpleAuthenticatedViewpointSerializer(SimpleViewpointSerializer):
    status = serializers.SerializerMethodField()

    class Meta:
        model = Viewpoint
        fields = ('id', 'label', 'picture', 'point', 'status')

    def get_status(self, obj):
        """
        :return: string (missing, draft, submitted, accepted)
        """
        # Get only pictures created for the campaign
        try:
            last_pic = obj.ordered_pics[0]
            if last_pic.created_at < obj.created_at:
                return settings.STATES.CHOICES_DICT[settings.STATES.MISSING]
            return settings.STATES.CHOICES_DICT[last_pic.state]
        except IndexError:
            return settings.STATES.CHOICES_DICT[settings.STATES.MISSING]


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


class DetailAuthenticatedCampaignNestedSerializer(serializers.ModelSerializer):
    owner = serializers.ReadOnlyField(source='owner.email')
    viewpoints = SimpleAuthenticatedViewpointSerializer(many=True, read_only=True)

    class Meta(CampaignSerializer.Meta):
        model = Campaign
        fields = '__all__'


class ListCampaignNestedSerializer(CampaignSerializer):
    picture = PermissiveImageFieldSerializer(
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
        fields = ('label', 'assignee', 'picture', 'statistics', 'status')


class PictureSerializer(serializers.ModelSerializer):
    owner = UserProfileSerializer(read_only=True)
    file = VersatileImageFieldSerializer('tropp')

    class Meta:
        model = Picture
        fields = '__all__'


class SimplePictureSerializer(PictureSerializer):
    class Meta:
        model = Picture
        fields = ('id', 'date', 'file', 'owner', 'properties')


class ViewpointSerializerWithPicture(serializers.ModelSerializer):
    picture_ids = serializers.PrimaryKeyRelatedField(
        source='pictures',
        queryset=Picture.objects.all(),
        required=False,
        many=True,
    )
    pictures = SimplePictureSerializer(many=True, read_only=True)
    related = RelatedDocumentFileSerializer(many=True, read_only=True)
    point = GeometryField(source='point.geom')

    class Meta:
        model = Viewpoint
        fields = ('id', 'label', 'properties', 'point', 'picture_ids',
                  'pictures', 'related')

    def create(self, validated_data):
        point_data = validated_data.pop('point', None)
        layer, created = Layer.objects.get_or_create(
            name=settings.TROPP_BASE_LAYER_NAME
        )
        feature = Feature.objects.create(
            geom=point_data.get('geom'),
            layer=layer,
            properties={},
        )
        validated_data.setdefault('point', feature)

        return super().create(validated_data)

    def update(self, instance, validated_data):
        point_data = validated_data.pop('point', None)
        if point_data:
            feature = instance.point
            feature.geom = point_data.get('geom')
            feature.save()

        # Remove pictures no longer associated with viewpoint
        if 'pictures' in validated_data:
            picture_ids = [p.pk for p in validated_data['pictures']]
            instance.pictures.exclude(pk__in=picture_ids).delete()

        return super().update(instance, validated_data)


class ViewpointLabelSerializer(serializers.ModelSerializer):
    class Meta:
        model = Viewpoint
        fields = ('id', 'label')
