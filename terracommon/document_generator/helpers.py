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

    def get_pdf(self, data=None):
        odt = self.get_odt(data=data)
        response = requests.post(
            url=settings.CONVERTIT_URL,
            files={'file': odt, },
            data={'to': 'application/pdf', }
        )
        response.raise_for_status()
        return response.content


class CachedDocument(File):
    def __init__(self, file, name=None):
        super().__init__(file, name=name)
        self.url = f'{settings.MEDIA_URL}{self.name}'

    def remove(self):
        os.remove(self.name)
