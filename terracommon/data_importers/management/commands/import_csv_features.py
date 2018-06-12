import argparse
import csv
import sys

from django.core.management import BaseCommand
from django.utils.translation import ugettext as _

from terracommon.terra.helpers import GeometryDefiner
from terracommon.terra.models import Layer


class Command(BaseCommand):
    help = _('Import insee data from csv to db.')

    pk_properties = {
        'insee': ['CODGEO', ],
        'companies': ['SIREN', 'NIC'],
    }

    def add_arguments(self, parser):
        parser.add_argument(
            '--csv-type',
            choices=self.pk_properties.keys(),
            required=True,
            action='store',
            dest='csv_type',
            help=_('Define the type of feature to import')
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
        layer_name = options.get('csv_type')
        insee_layer = Layer.objects.get_or_create(name=layer_name)[0]

        if options['bulk']:
            insee_layer.features.all().delete()

        reader = csv.DictReader(options.get('source'),
                                delimiter=options.get('delimiter'),
                                quotechar='"')

        geometry_columns = {
            GeometryDefiner.LONGITUDE: options.get('longitude'),
            GeometryDefiner.LATITUDE: options.get('latitude')
        }
        geometry_columns_filtered = {k: v for k, v in geometry_columns.items()
                                     if v is not None}

        insee_layer.from_csv_dictreader(
            reader,
            self.pk_properties.get(layer_name, []),
            options.get('init'),
            options.get('creations_per_transaction'),
            options.get('fast'),
            geometry_columns_filtered
        )
