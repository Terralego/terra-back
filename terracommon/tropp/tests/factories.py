import factory
from django.utils import timezone
from factory.django import FileField

from terracommon.tropp.models import Campaign, Picture, Viewpoint


class CampaignFactory(factory.DjangoModelFactory):
    owner = factory.SubFactory(
        'terracommon.accounts.tests.factories.TerraUserFactory'
    )
    assignee = factory.SubFactory(
        'terracommon.accounts.tests.factories.TerraUserFactory'
    )

    class Meta:
        model = Campaign


class ViewpointFactory(factory.DjangoModelFactory):
    point = factory.SubFactory(
        'geostore.tests.factories.FeatureFactory'
    )
    pictures = factory.RelatedFactory(
        'terracommon.tropp.tests.factories.PictureFactory', 'viewpoint'
    )

    class Meta:
        model = Viewpoint


class PictureFactory(factory.DjangoModelFactory):
    owner = factory.SubFactory(
        'terracommon.accounts.tests.factories.TerraUserFactory'
    )
    date = timezone.datetime(2018, 1, 1, tzinfo=timezone.utc)
    file = FileField(from_path='terracommon/tropp/tests/placeholder.jpg')

    class Meta:
        model = Picture
