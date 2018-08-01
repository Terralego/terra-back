import logging
import os

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.management import call_command
from django.test import TestCase

from terracommon.terra.transformations import set_geometry_from_options

UserModel = get_user_model()


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
        log_record = cm.records[0]
        self.assertEqual(set_geometry_from_options.__name__,
                         log_record.funcName)
        self.assertIn('019778745', log_record.msg)  # SIREN key
        self.assertIn('00018', log_record.msg)  # NIC key

    def test_csv_user_import(self):
        groups = ['group1', 'group2']
        for group in groups:
            Group.objects.create(name=group)

        test_file = os.path.join(os.path.dirname(__file__), 'test_users.csv')
        call_command('import_csv_users',
                     f'-cs={test_file}',
                     '-u=email',
                     '--group=group1',
                     '--group=group2')

        self.assertEqual(2, UserModel.objects.all().count())

        for user in UserModel.objects.all():
            self.assertListEqual(groups, [g.name for g in user.groups.all()])
