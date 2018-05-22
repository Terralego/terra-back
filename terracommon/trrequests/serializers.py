from rest_framework import serializers

from terracommon.terra.serializers import TerraUserSerializer
from .models import Comment, Organization, UserRequest


class UserRequestSerializer(serializers.ModelSerializer):
    owner = TerraUserSerializer(read_only=True)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        request_user = self.context['request'].user
        self.fields['organization'].queryset = (
                            Organization.objects.filter(owner=request_user))

    class Meta:
        model = UserRequest
        fields = '__all__'
        read_only_fields = ('owner', )


class OrganizationSerializer(serializers.ModelSerializer):

    class Meta:
        model = Organization
        fields = '__all__'
        read_only_fields = ('owner', )


class CommentSerializer(serializers.ModelSerializer):
    owner = TerraUserSerializer(read_only=True)

    class Meta:
        model = Comment
        fields = '__all__'
        read_only_fields = ('owner', 'userrequest',)
