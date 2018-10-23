import hashlib
import io
import logging
import os
import zipfile

import jinja2
import requests
from django.conf import settings
from django.core.files import File
from django.utils.functional import cached_property
from docxtpl import DocxTemplate
from jinja2 import TemplateSyntaxError
from requests.exceptions import ConnectionError, HTTPError

from terracommon.document_generator.models import DownloadableDocument

from .filters import timedelta_filter

logger = logging.getLogger(__name__)


class DocumentGenerator:
    def __init__(self, downloadabledoc):
        if not isinstance(downloadabledoc, DownloadableDocument):
            raise TypeError("downloadabledoc must be a DownloadableDocument")
        self.template = downloadabledoc.document.documenttemplate.path
        self.datamodel = downloadabledoc.linked_object

    def get_docx(self, data):
        doc = DocxTemplator(self.template)
        jinja_env = jinja2.Environment()
        jinja_env.filters.update(self.filters)
        doc.render(context=data, jinja_env=jinja_env)
        return doc.save()

    def get_pdf(self, reset_cache=False):
        cachepath = os.path.join(
            self.datamodel.__class__.__name__,
            f'{self._document_checksum}_{self.datamodel.pk}.pdf'
        )
        cache = CachedDocument(cachepath)

        if not cache.exist or reset_cache:
            if reset_cache:
                cache.remove()

            self._get_docx_as_pdf(cache)

        return cache.name

    def _get_docx_as_pdf(self, cache):
        serializer = self.datamodel.get_serializer()
        serialized_model = serializer(self.datamodel)

        try:
            odt = self.get_docx(data=serialized_model.data)
        except FileNotFoundError:
            # remove newly created file
            # for caching purpose
            cache.remove()
            logger.warning(f"File {self.template} not found.")
            raise
        except TemplateSyntaxError as e:
            cache.remove()
            logger.warning(f'TemplateSyntaxError for {self.template} '
                           f'at line {e.lineno}: {e.message}')
            raise
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
            logger.warning(f"Http error {response.status_code}")
            raise
        except ConnectionError:
            cache.remove()
            logger.warning("Connection error")
            raise

        with cache.open() as cached_pdf:
            cached_pdf.write(response.content)

    @cached_property
    def _document_checksum(self):
        """ return the md5 checksum of self.template """
        content = None
        if isinstance(self.template, io.IOBase):
            content = self.template.read()
        else:
            content = bytes(self.template, 'utf-8')

        return hashlib.md5(content)

    filters = {
        'timedelta_filter': timedelta_filter
    }


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

    def remove(self):
        os.remove(self.name)


class DocxTemplator(DocxTemplate):
    def post_processing(self, docx_bytesio):
        if self.crc_to_new_media or self.crc_to_new_embedded:
            backup_bytesio = io.BytesIO()

            with zipfile.ZipFile(docx_bytesio) as zin:
                with zipfile.ZipFile(backup_bytesio, 'w') as zout:
                    for item in zin.infolist():
                        buf = zin.read(item.filename)

                        if (item.filename.startwith('word/media/')
                                and item.CRC in self.crc_to_new_media):
                            zout.writestr(item,
                                          self.crc_to_new_media[item.CRC])
                        elif (item.filename.startwith('word/embeddings/')
                              and item.CRC in self.crc_to_new_embedded):
                            zout.writestr(item,
                                          self.crc_to_new_embedded[item.CRC])
                        else:
                            zout.writestr(item, buf)
            return backup_bytesio
        return docx_bytesio

    def save(self):
        docx_bytesio = io.BytesIO()
        self.pre_processing()
        self.docx.save(docx_bytesio)
        return self.post_processing(docx_bytesio)
