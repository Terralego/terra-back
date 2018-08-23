from django.core.management import BaseCommand
from django.utils.translation import ugettext as _

from terracommon.events.signals import event


class Command(BaseCommand):
    help = _('Sends signal related to an action passed as parameter')

    def add_arguments(self, parser):
        parser.add_argument('-a', '--action',
                            required=False,
                            action='store',
                            dest='action',
                            help=_('Specify action name'),
                            )
        parser.add_argument('-i', '--instance',
                            required=False,
                            action='store',
                            dest='instance',
                            help=_('Specify instance pk'),
                            )
        parser.add_argument('-u', '--user',
                            required=False,
                            action='store',
                            dest='user',
                            help=_('Specify user pk'),
                            )
        parser.add_argument('-k', '--kwargs',
                            required=False,
                            default=[],
                            action='append',
                            dest='kwargs',
                            help=_('Allow to pass any type of argument'),
                            )

    def handle(self, *args, **options):
        overloaded_keys = ['action', 'instance', 'user']
        required_keys = ['action']

        kwargs = dict()

        for kwarg in options.get('kwargs'):
            key, value = kwarg.split(':')
            kwargs[key] = value

        for key in overloaded_keys:
            if options.get(key):  # Passed in argument
                kwargs[key] = options[key]
            elif not kwargs.get(key):  # Missing value
                if key in required_keys:
                    continue  # Keep the exception happen
                kwargs[key] = None

        event.send(self.__class__, **kwargs)
