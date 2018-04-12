import logging

from django.apps import apps
from django.db import transaction
from django.core.management.base import BaseCommand
from django.utils.functional import cached_property

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = "Populate database from all installed app's initialization modules"

    POPULATE_MODULE_NAME = 'populate'
    POPULATE_FN_NAME = 'load_datas'
    POPULATE_TEST_FN_NAME = 'load_test_datas'

    def add_arguments(self, parser):
        parser.add_argument('-d','--dry-run',
                            action="store_true",
                            help='Dry-run mode')
        parser.add_argument('-t','--test-datas',
                            action="store_true",
                            help='Load test datas')
        parser.add_argument('-l', '--list',
                            action="store_true",
                            help='List available modules')
        parser.add_argument('-m','--modules',
                            action="store",
                            nargs="?",
                            help="Load data for this modules")

    def handle(self, *args, **options):
        if options.get('list', False):
            self.stdout.write('Applications with populate modules:')
            for app_name in self.available_modules.keys():
                self.stdout.write('  - {}'.format(app_name))
            exit(0)

        load_fn = self.get_modules_fn(options.get('test_datas'))

        sid = transaction.savepoint()

        for app_name, load_data_fn in load_fn.items():
            with transaction.atomic():
                self.stdout.write('Loading data for {}'.format(app_name))
                load_data_fn()
            
        if options.get('dry_run'):
            transaction.savepoint_rollback(sid)


    def get_modules_fn(self, test=False):
        fn_name = self.POPULATE_TEST_FN_NAME if test else self.POPULATE_FN_NAME
        return { app_name: getattr(module, fn_name) for app_name, module in self.available_modules.items() if hasattr(module, fn_name) }

    @cached_property
    def available_modules(self):
        available_modules = {}
        for app_name, app_config in apps.app_configs.items():
            try:
                """ Modules must be loaded else they are not present un modules attributes """
                __import__("{}.{}".format(app_config.module.__package__, self.POPULATE_MODULE_NAME))
            except ModuleNotFoundError:
                logger.debug('Application {} has no populate module'.format(app_name))

            if hasattr(app_config.module, self.POPULATE_MODULE_NAME):
                available_modules[app_name] = getattr(app_config.module, self.POPULATE_MODULE_NAME)

        return available_modules