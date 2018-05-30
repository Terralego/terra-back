import factory

from terracommon.trrequests.models import Organization


class OrganizationFactory(factory.DjangoModelFactory):
    properties = {}

    class Meta:
        model = Organization
