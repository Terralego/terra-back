import argparse
import csv
import sys

from django.core.management import BaseCommand
from django.utils.translation import ugettext as _

from terracommon.terra.helpers import GeometryDefiner
from terracommon.terra.models import Layer


class Command(BaseCommand):
    help = _('Import insee data from csv to db.')

    def add_arguments(self, parser):
        parser.add_argument(
            '--layer',
            required=True,
            action='store',
            dest='layer',
            help=_('Specify layer name')
        )
        parser.add_argument(
            '--key',
            required=True,
            action='append',
            dest='pk_properties',
            help=_("Define primary keys of this data"
                   "Example with companies:"
                   "--key=SIREN --key=NIC"
                   "Example with INSEE:"
                   "--key=code_insee")
        )
        parser.add_argument(
            '--init',
            action='store_true',
            dest='init',
            default=False,
            help=_('Improve performance of initial import')
        )
        parser.add_argument(
            '--bulk',
            action='store_true',
            dest='bulk',
            default=False,
            help=_('Delete all stored INSEE data. DO NOT USE IN PROD.')
        )
        parser.add_argument(
            '--source',
            dest='source',
            type=argparse.FileType('r', encoding='iso-8859-15'),
            default=sys.stdin,
            required=True,
            help=_('Specify source file path'),
        )
        parser.add_argument(
            '--delimiter',
            action='store',
            dest='delimiter',
            default=';',
            required=False,
            help=_('Specify CSV delimiter')
        )
        parser.add_argument(
            '--creations-per-transaction',
            dest='creations_per_transaction',
            type=int,
            default=1000,
            help=_('Number of operations per transaction')
        )
        parser.add_argument(
            '--longitude',
            required=False,
            action='store',
            dest='longitude',
            help=_('Name of longitude column')
        )
        parser.add_argument(
            '--latitude',
            required=False,
            action='store',
            dest='latitude',
            help=_('Name of latitude column')
        )
        parser.add_argument('--fast',
                            action='store_true',
                            default=False,
                            help="If present and it's not an initial import"
                                 " will speed up features creation. But no"
                                 " rollback is possible. If something broke"
                                 " up during import, the import will stop "
                                 " with half data in database.")

    def handle(self, *args, **options):
        layer_name = options.get('layer')
        layer = Layer.objects.get_or_create(name=layer_name)[0]

        if options['bulk']:
            layer.features.all().delete()

        reader = csv.DictReader(options.get('source'),
                                delimiter=options.get('delimiter'),
                                quotechar='"')

        geometry_columns = {
            GeometryDefiner.LONGITUDE: options.get('longitude'),
            GeometryDefiner.LATITUDE: options.get('latitude')
        }
        geometry_columns_filtered = {k: v for k, v in geometry_columns.items()
                                     if v is not None}

        layer.from_csv_dictreader(
            reader,
            options.get('pk_properties'),
            options.get('init'),
            options.get('creations_per_transaction'),
            options.get('fast'),
            geometry_columns_filtered
        )
