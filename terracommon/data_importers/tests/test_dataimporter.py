import os

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.management import call_command
from django.test import TestCase


UserModel = get_user_model()


class DataImporterTestCase(TestCase):
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
