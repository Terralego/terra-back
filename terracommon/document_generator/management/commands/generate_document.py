import argparse
import json
import logging
import sys

from django.core.management import BaseCommand
from django.utils.translation import ugettext as _

from terracommon.document_generator.helpers import DocumentGenerator

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = _('Completion and document file conversion')

    possible_types = ['odt', 'pdf']

    def add_arguments(self, parser):
        parser.add_argument('--template',
                            dest='template',
                            type=argparse.FileType('rb'),
                            default=sys.stdin,
                            required=True,
                            help=_('ODT model to be completed'),
                            )
        parser.add_argument('--data',
                            dest='data',
                            help=_('Data to use to complete'),
                            )
        parser.add_argument('--type',
                            choices=self.possible_types,
                            required=True,
                            action='store',
                            dest='output_type',
                            help=_('Extension of the output file')
                            )
        parser.add_argument('--ouput',
                            dest='output_path',
                            type=argparse.FileType('wb'),
                            default=sys.stdin,
                            required=False,
                            help=_(''),
                            )

    def handle(self, *args, **options):
        dg = DocumentGenerator(options.get('template'))

        data = {}
        if options.get('data'):
            data = json.loads(options.get('data'))
        else:
            logger.warning('No data passed')

        if options.get('output_type') == 'odt':
            result = dg.get_odt(data=data)
        else:  # pdf
            result = dg.get_pdf(data=data)

        if options.get('output_path'):
            return options.get('output_path').write(result)
        else:
            return result
