from django.apps import AppConfig


class EventsConfig(AppConfig):
    name = 'terracommon.events'

    def ready(self):
        from . import signals
        if signals:
            return True
