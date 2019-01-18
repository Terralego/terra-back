from django.apps import AppConfig
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured


class TroppConfig(AppConfig):
    name = 'terracommon.tropp'

    def ready(self):
        import terracommon.tropp.signals  # noqa
        if 'versatileimagefield' not in settings.INSTALLED_APPS:
            raise ImproperlyConfigured(
                f"'{self.name}' needs 'versatileimagefield' in INSTALLED_APPS"
            )
