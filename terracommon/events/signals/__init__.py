import logging

from django.conf import settings
from django.dispatch import Signal
from django.utils.module_loading import import_string

from terracommon.events.models import EventHandler

logger = logging.getLogger(__name__)

event = Signal(providing_args=['action', 'logged_user'])


def signal_event_proxy(sender, action, instance, user, *args, **kwargs):
    for handler in (EventHandler.objects
                                .filter(action=action)
                                .order_by('priority')):
        try:
            args = {
                'instance': instance,
                'user': user,
                **kwargs
            }

            handler_class = import_string(handler.handler)
            try:
                executor = handler_class(handler.action,
                                         handler.settings,
                                         **args)

                if executor.valid_condition():
                    executor()
            except Exception as e:
                if settings.DEBUG:
                    raise
                else:
                    logger.error('Handler error: %s',
                                 e,
                                 extra={'handler': handler.handler})
        except ImportError as e:
            logger.error(f"An error occured loading {handler.handler}: {e}")


event.connect(signal_event_proxy)
