import factory

from terracommon.trrequests.models import UserRequest, Organization


class UserRequestFactory(factory.DjangoModelFactory):
    owner = factory.SubFactory('terracommon.terra.tests.factories.TerraUserFactory')
    layer = factory.SubFactory('terracommon.terra.tests.factories.LayerFactory')
    state = 0

    class Meta:
        model = UserRequest


class OrganizationFactory(factory.DjangoModelFactory):
    properties = {}

    class Meta:
        model = Organization
