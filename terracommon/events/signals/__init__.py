import logging

from django.dispatch import Signal
from django.utils.module_loading import import_string

from terracommon.events.models import EventHandler

logger = logging.getLogger(__name__)

event = Signal(providing_args=['action', 'logged_user'])


def signal_event_proxy(sender, action, instance, user, *args, **kwargs):

    for handler in EventHandler.objects.filter(action=action):
        try:
            args = {
                'instance': instance,
                'user': user,
                **kwargs
            }

            handler_class = import_string(handler.handler)
            executor = handler_class(handler.action, handler.settings, args)

            if executor.is_callable():
                executor()
        except ImportError as e:
            logger.error(f"An error occured loading {handler.handler}: {e}")


event.connect(signal_event_proxy)
