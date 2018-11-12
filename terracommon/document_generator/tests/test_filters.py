from datetime import datetime, timedelta

from django.test import TestCase

from terracommon.datastore.models import DataStore
from terracommon.document_generator.filters import (timedelta_filter,
                                                    todate_filter,
                                                    translate_filter)


class FilterTestCase(TestCase):
    def setUp(self):
        self.date = datetime.now()

    def test_timedelta_filter(self):
        # test with not value for delta_days
        date_result = timedelta_filter(str(self.date))
        self.assertEqual(date_result, self.date.date())

        # test with a delta_days value
        delta_days = 7
        date_result = timedelta_filter(str(self.date), delta_days=delta_days)
        self.assertEqual(
            date_result,
            (self.date - timedelta(days=delta_days)).date()
        )

        # test with a negative delat_days value
        delta_days = -7
        date_result = timedelta_filter(str(self.date), delta_days=delta_days)
        self.assertEqual(
            date_result,
            (self.date - timedelta(days=delta_days)).date()
        )

    def test_translate_filter(self):
        # Create a correspondence object in the datastore
        DataStore.objects.create(
            key='test.translate',
            value={'tree': 'arbre'},
        )

        # test without datastore key first
        result = translate_filter('tree')
        self.assertEqual(result, 'tree')

        # test with a datastore key
        result = translate_filter('tree', datastorekey='test.translate')
        self.assertEqual(result, 'arbre')

    def test_todate_filter(self):
        date_result = todate_filter(str(self.date))
        self.assertEqual(date_result, self.date.date())
