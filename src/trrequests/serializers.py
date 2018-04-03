from rest_framework import serializers

from .models import Request, Organization


class RequestSerializer(serializers.ModelSerializer):

    def __init__(self, *args, **kwargs):
        super(RequestSerializer, self).__init__(*args, **kwargs)
        request_user = self.context['request'].user
        self.fields['organization'].queryset = (
                            Organization.objects.filter(owner=request_user))
        print(dir(self.fields['organization']))

    class Meta:
        model = Request
        exclude = ('owner', )


class OrganizationSerializer(serializers.ModelSerializer):

    class Meta:
        model = Organization
        exclude = ('owner', )
