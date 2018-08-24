import os

import requests
from django.conf import settings
from django.core.files import File
from django.db.models import Model
from requests.exceptions import HTTPError
from secretary import Renderer


class DocumentGenerator:
    def __init__(self, template):
        self.template = template

    def get_odt(self, data=None):
        engine = Renderer()
        return engine.render(self.template, data=data)

    def get_pdf(self, data=None):
        if not isinstance(data, Model):
            raise TypeError("data must be a django Model")

        cachepath = os.path.join(data.__class__.__name__, f'{data.pk}.pdf')
        cache = CachedDocument(cachepath)

        if cache.exist:
            return cache

        try:
            odt = self.get_odt(data=data)
        except FileNotFoundError:
            # remove newly created file
            # for caching purpose
            cache.remove()
            raise
        else:
            try:
                response = requests.post(
                    url=settings.CONVERTIT_URL,
                    files={'file': odt, },
                    data={'to': 'application/pdf', }
                )
                response.raise_for_status()
            except HTTPError:
                # remove newly created file
                # for caching purpose
                cache.remove()
                raise
            else:
                cached_pdf = cache.open()
                cached_pdf.write(response.content.read())
                return cached_pdf


class CachedDocument(File):
    cache_root = 'cache'

    def __init__(self, filename, mode='xb+'):
        self.pathname = os.path.join(self.cache_root, filename)

        if not os.path.isfile(self.pathname):
            self.exist = False

            # dirname is not current dir
            if os.path.dirname(self.pathname) != '':
                os.makedirs(os.path.dirname(self.pathname), exist_ok=True)

            super().__init__(open(self.pathname, mode=mode))
        else:
            self.exist = True
            super().__init__(open(self.pathname))

        self.url = f'{settings.MEDIA_URL}{self.name}'

    def remove(self):
        os.remove(self.name)
