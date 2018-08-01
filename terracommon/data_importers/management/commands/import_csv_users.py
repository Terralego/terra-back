import argparse
import csv
import sys

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.management import BaseCommand
from django.db import transaction
from django.utils.translation import ugettext as _

UserModel = get_user_model()


class Command(BaseCommand):
    help = _('Import users from csv to database.')

    def add_arguments(self, parser):
        parser.add_argument('-cd', '--delimiter',
                            action='store',
                            dest='delimiter',
                            default=';',
                            required=False,
                            help=_('Specify CSV delimiter')
                            )
        parser.add_argument('-cq', '--quotechar',
                            action='store',
                            dest='quotechar',
                            default='"',
                            required=False,
                            help=_('Specify CSV quotechar')
                            )
        parser.add_argument('-cs', '--source',
                            dest='source',
                            type=argparse.FileType('r',
                                                   encoding='iso-8859-15'),
                            default=sys.stdin,
                            required=True,
                            help=_('Specify CSV path'),
                            )
        parser.add_argument('-u', '--username-field',
                            required=True,
                            action='store',
                            dest='user_field',
                            help=_("Define the column used as userfield, "
                                   "others are put in properties")
                            )
        parser.add_argument('-p', '--password-field',
                            required=False,
                            action='store',
                            dest='password_field',
                            help=_("Define the column used as userfield, "
                                   "others are put in properties")
                            )
        parser.add_argument('-g', '--group',
                            required=False,
                            action='append',
                            dest='group',
                            help=_("Default group of newly created users")
                            )

    @transaction.atomic
    def handle(self, *args, **options):
        username, password = (options.get('user_field'),
                              options.get('password_field'))

        reader = csv.DictReader(options.get('source'),
                                delimiter=options.get('delimiter'),
                                quotechar=options.get('quotechar'))

        fields = [fieldname
                  for fieldname in reader.fieldnames
                  if fieldname not in ['', username, password]]

        groups = Group.objects.filter(name__in=options.get('group'))

        for row in reader:
            user = UserModel.objects.create(
                **{
                    UserModel.USERNAME_FIELD: row[username],
                    'properties': {field: row.get(field) for field in fields},
                }
            )
            if password:
                user.set_password(row[password])
            else:
                user.set_unusable_password()

            user.groups.add(*groups)
