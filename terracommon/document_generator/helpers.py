import os

import requests
from django.conf import settings
from django.core.files import File
from secretary import Renderer


class DocumentGenerator:
    def __init__(self, template):
        self.template = template

    def get_odt(self, data=None):
        engine = Renderer()
        return engine.render(self.template, data=data)

    def get_pdf(self, data=None, filename=None):
        if filename is None or not os.path.isfile(filename):
            odt = self.get_odt(data=data)
            response = requests.post(
                url=settings.CONVERTIT_URL,
                files={'file': odt, },
                data={'to': 'application/pdf', }
            )
            response.raise_for_status()

            if filename is None:
                return response.content
            else:
                # Caching the pdf document
                cached_pdf = CachedDocument(filename, mode='wb+')
                pdf = response.content.open()
                cached_pdf.write(pdf.read())
                return cached_pdf
        else:
            cached_pdf = CachedDocument(filename)
            return cached_pdf


class CachedDocument(File):
    def __init__(self, filename, mode='wb'):
        if not os.path.isfile(filename):
            if os.path.dirname(filename) != '':
                os.makedirs(os.path.dirname(filename), exist_ok=True)
            super().__init__(open(filename, mode='wb'), name=filename)
        else:
            super().__init__(open(filename))

        self.url = f'{settings.MEDIA_URL}{self.name}'

    def remove(self):
        os.remove(self.name)
