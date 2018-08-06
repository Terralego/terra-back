import os

import requests
from django.conf import settings
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


class CachedDocument:
    """ Manage document caching through filesystem """
    cache_root = os.path.join(settings.MEDIA_ROOT, 'cache/')

    def __init__(self, path):
        self.path = os.path.join(self.cache_root, path)

    def create_cache(self, content, writing_mode):
        """ Create a file cache for a given content

        content: data to store in cache file
        file_type: 'wb' or 'w' for binary or text.
        """
        allowed_mode = ['w', 'wb']
        if writing_mode not in allowed_mode:
            raise ValueError("writting mode should be 'w' or 'wb'")

        cache_dir = os.path.dirname(self.path)
        if not os.path.isdir(cache_dir):
            os.makedirs(cache_dir)

        with open(self.path, writing_mode) as f:
            f.write(content)

    def delete_cache(self):
        """ Remove a cache file """
        os.remove(self.path)

    def is_cached(self):
        """ check if the file exist """
        return os.path.isfile(self.path)
