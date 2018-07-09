import logging
import os

from django.core.management import call_command
from django.test import TestCase


class DataImporterTestCase(TestCase):
    def test_command_launch(self):
        test_file = os.path.join(os.path.dirname(__file__), 'test.csv')

        with self.assertLogs(level=logging.WARNING) as cm:
            call_command('import_csv_features',
                         ('--operation=terracommon.data_importers.tests'
                          '.test_dataimporter_functions.empty_operation'),
                         ('--operation=terracommon.terra.transformations'
                          '.set_geometry_from_options'),
                         '--layer=companies',
                         '--key=SIREN',
                         '--key=NIC',
                         f'--source={test_file}')
        self.assertEqual(len(cm.records), 1)
        self.assertIn('can not define geometry for:', cm.records[0].msg)
