import factory

from terracommon.trrequests.models import UserRequest


class UserRequestFactory(factory.DjangoModelFactory):
    owner = factory.SubFactory(
        'terracommon.accounts.tests.factories.TerraUserFactory')
    layer = factory.SubFactory(
        'terracommon.terra.tests.factories.LayerFactory')
    state = 0

    class Meta:
        model = UserRequest
