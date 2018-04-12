import logging

from django.apps import apps
from django.db import transaction
from django.core.management.base import BaseCommand

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = "Populate database from all installed app's initialization modules"

    POPULATE_MODULE_NAME = 'populate'

    def add_arguments(self, parser):
        parser.add_argument('-t','--test-datas',
                            action="store_true",
                            help='Load test datas')
        parser.add_argument('-l', '--list',
                            action="store_true",
                            help='List available modules')

    def handle(self, *args, **options):
        pass

    def get_available_modules(self):
        available_modules = []
        for app_name, app_config in apps.app_configs.items():
            try:
                """ Modules must be loaded else they are not present un modules attributes """
                __import__("{}.{}".format(app_config.module.__package__, self.POPULATE_MODULE_NAME))
            except ModuleNotFoundError:
                logger.debug('Application {} has no populate module'.format(app_name))

            if hasattr(app_config.module, self.POPULATE_MODULE_NAME):
                available_modules.append(
                    (app_name, getattr(app_config.module, self.POPULATE_MODULE_NAME))
                    )

        return available_modules