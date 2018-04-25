import argparse
import csv
import sys

from django.contrib.gis.geos.point import Point
from django.core.management import BaseCommand
from django.db import transaction
from django.utils.translation import ugettext as _

from terra.models import Layer, Feature


class Command(BaseCommand):
    help = _('Import insee data from csv to db.')

    def add_arguments(self, parser):
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
            dest='path',
            type=argparse.FileType('r'),
            default=sys.stdin,
            required=True,
            help=_('Specify source file path'),
        )
        parser.add_argument(
            '--creations-per-transaction',
            dest='creations_per_transaction',
            type=int,
            default=1000,
            help=_('Number of operations per transaction')
        )

    def handle(self, *args, **options):
        insee_layer = Layer.objects.get_or_create(name='insee')[0]
        if options['bulk']:
            Feature.objects.filter(layer=insee_layer).delete()
        with open(options['path'].name, encoding="iso8859-15") as csvfile:
            reader = csv.DictReader(csvfile, delimiter=';', quotechar='"')
            if options['init']:
                entries = []
                for i, row in enumerate(reader):
                    entries.append(Feature(
                        geom=Point(),
                        properties=row,
                        layer=insee_layer,
                    ))
                    if len(entries) == options['creations_per_transaction']:
                        with transaction.atomic():
                            Feature.objects.bulk_create(entries)
                        entries.clear()
                if entries:
                    with transaction.atomic():
                        Feature.objects.bulk_create(entries)
                    entries.clear()
            else:
                for row in reader:
                    Feature.objects.update_or_create(
                        defaults={
                            'geom': Point(),
                            'properties': row,
                            'layer': insee_layer,
                        },
                        layer=insee_layer,
                        properties__CODGEO=row.get('CODGEO', ''),
                    )
