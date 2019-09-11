import factory

from terracommon.trrequests.models import Comment, UserRequest


class UserRequestFactory(factory.DjangoModelFactory):
    owner = factory.SubFactory(
        'terracommon.accounts.tests.factories.TerraUserFactory')
    layer = factory.SubFactory(
        'geostore.tests.factories.LayerFactory')
    state = 0

    class Meta:
        model = UserRequest


class CommentFactory(factory.DjangoModelFactory):
    owner = factory.SubFactory(
        'terracommon.accounts.tests.factories.TerraUserFactory')
    userrequest = factory.SubFactory(
        'terracommon.trrequests.tests.factories.UserRequestFactory')

    class Meta:
        model = Comment
