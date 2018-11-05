import datetime

import factory
from factory.fuzzy import FuzzyDate

from terracommon.tropp.models import Picture, Viewpoint


class ViewpointFactory(factory.DjangoModelFactory):
    point = factory.SubFactory(
        'terracommon.terra.tests.factories.FeatureFactory'
    )

    class Meta:
        model = Viewpoint


class PictureFactory(factory.DjangoModelFactory):
    owner = factory.SubFactory(
        'terracommon.accounts.tests.factories.TerraUserFactory'
    )
    date = FuzzyDate(datetime.date(2008, 1, 1))

    class Meta:
        model = Picture
