import datetime
import hashlib
import io
import logging
import os
import shutil
import subprocess
import zipfile
from tempfile import NamedTemporaryFile, TemporaryDirectory

import jinja2
import magic
from django.conf import settings
from django.core.files import File
from django.http import HttpResponse, HttpResponseForbidden
from django.template import Context, Template
from django.template.exceptions import \
    TemplateSyntaxError as DjangoTemplateSyntaxError
from django.utils.functional import cached_property
from docx.shared import Mm
from docxtpl import DocxTemplate, InlineImage
from jinja2 import TemplateSyntaxError
from magic import from_file
from weasyprint import HTML

from terracommon.document_generator.models import DownloadableDocument

from .filters import (b64_to_inlineimage, timedelta_filter, todate_filter,
                      translate_filter)

logger = logging.getLogger(__name__)


class DocumentGenerator:

    def __init__(self, downloadabledoc):
        if not isinstance(downloadabledoc, DownloadableDocument):
            raise TypeError("downloadabledoc must be a DownloadableDocument")
        self.template = downloadabledoc.document.documenttemplate.path
        try:
            self.type = from_file(self.template, mime=True)
        except FileNotFoundError:
            logger.warning(f"File {self.template} not found.")
            raise
        self.datamodel = downloadabledoc.linked_object
        self.mime_type_mapping = {
            'text/html': self._get_html_as_pdf,
            'application/octet-stream': self._get_docx_as_pdf,
        }

    def get_docx(self, data):
        doc = DocxTemplator(self.template)

        updated_data = (self._get_image(data, doc)
                        if data.get('documents')
                        else data)
        updated_data['tpl'] = doc  # doc is needed in a custom jinja filter
        jinja_env = jinja2.Environment()
        jinja_env.globals['now'] = datetime.datetime.now
        jinja_env.filters.update(self.filters)

        # render is perform in a temp dir
        # Because some custom jinja filter used temp files
        # which are not removed during render
        with TemporaryDirectory() as tmpdir:
            updated_data['tmpdir'] = tmpdir  # used by tempfile in custom filter
            doc.render(context=updated_data, jinja_env=jinja_env)

        # tmpdir is not removed if not empty. Ensure it's cleaned anyway
        if os.path.isdir(tmpdir):
            shutil.rmtree(tmpdir)
        return doc.save()

    def get_html(self, data):
        with open(self.template, 'r') as read_file:
            template = Template(read_file.read())
        html_content = template.render(Context(data))
        return html_content

    def get_pdf(self, reset_cache=False):
        cachepath = os.path.join(
            self.datamodel.__class__.__name__,
            f'{self._document_checksum}_{self.datamodel.pk}.pdf'
        )

        cache = CachedDocument(cachepath)
        if cache.exist:
            reset_cache = self.datamodel.updated_at.timestamp() > os.path.getmtime(cache.name)

        if not cache.exist or reset_cache:
            if reset_cache:
                cache.clear()

            serializer = (self.datamodel.get_pdf_serializer()
                          if hasattr(self.datamodel, 'get_pdf_serializer')
                          else self.datamodel.get_serializer())
            serialized_model = serializer(self.datamodel)

            self.mime_type_mapping[self.type](cache, serialized_model)

        return cache.name

    def _get_html_as_pdf(self, cache, serialized_model):
        try:
            html_content = self.get_html(serialized_model.data)
        except DjangoTemplateSyntaxError:
            cache.remove()
            logger.warning(f'TemplateSyntaxError for {self.template}')
            raise
        pdf = HTML(string=html_content).write_pdf()
        with cache.open() as cached_pdf:
            cached_pdf.write(pdf)

    def _get_docx_as_pdf(self, cache, serialized_model):
        try:
            docx = self.get_docx(data=serialized_model.data)
        except TemplateSyntaxError as e:
            cache.remove()
            logger.warning(f'TemplateSyntaxError for {self.template} '
                           f'at line {e.lineno}: {e.message}')
            raise

        # Create a temporary docx file on disk so libreoffice can use it
        with TemporaryDirectory() as tmpdir, NamedTemporaryFile(mode='wb',
                                                                dir=tmpdir,
                                                                suffix='.docx') as tmp_docx:
            tmp_docx.write(docx.getvalue())  # docx is an io.BytesIO

            # Call libreoffice to convert docx to pdf
            subprocess.run([
                'lowriter',
                '--headless',
                '--convert-to',
                'pdf:writer_pdf_Export',
                '--outdir',
                tmpdir,
                tmp_docx.name
            ])

            # Get pdf name of the file created from libreoffice writer
            tmp_pdf_root = os.path.splitext(os.path.basename(tmp_docx.name))[0]
            tmp_pdf = os.path.join(tmpdir, f'{tmp_pdf_root}.pdf')

            with cache.open() as cached_pdf, open(tmp_pdf, 'rb') as pdf:
                cached_pdf.write(pdf.read())

            # We don't need it anymore
            os.remove(tmp_pdf)

    def _get_image(self, data, tpl):
        for document in data['documents']:
            img_path = os.path.join(settings.MEDIA_ROOT, document['document'])
            # Set as image of 170mm width
            document['document'] = InlineImage(tpl, img_path, width=Mm(170))
        return data

    @cached_property
    def _document_checksum(self):
        """ return the md5 checksum of self.template """
        content = None
        if isinstance(self.template, io.IOBase):
            content = self.template.read()
        else:
            content = bytes(self.template, 'utf-8')

        return hashlib.md5(content).hexdigest()

    # TODO make it a function in filters.py
    filters = {
        'timedelta_filter': timedelta_filter,
        'translate_filter': translate_filter,
        'todate_filter': todate_filter,
        'b64_to_inlineimage': b64_to_inlineimage,
    }


class CachedDocument(File):
    cache_root = 'cache'

    def __init__(self, filename):
        self.pathname = os.path.join(self.cache_root, filename)

        if not os.path.isfile(self.pathname):
            self.exist = False

            # dirname is not current dir
            if os.path.dirname(self.pathname) != '':
                os.makedirs(os.path.dirname(self.pathname), exist_ok=True)

            super().__init__(open(self.pathname, mode='xb+'))
        else:
            self.exist = True
            super().__init__(open(self.pathname, mode='rb'))

    def remove(self):
        self.close()
        os.remove(self.name)

    def clear(self, mode=None):
        self.remove()
        self.file = open(self.name, 'xb+')


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

    def save(self, *args, **kwargs):
        docx_bytesio = io.BytesIO()
        self.pre_processing()
        self.docx.save(docx_bytesio)
        return self.post_processing(docx_bytesio)


def get_media_response(request, data, permissions=None, headers=None):
    # For compatibility purpose
    content, url = None, None
    if isinstance(data, (io.IOBase, File)):
        content, url = data, data.url
    else:
        # https://docs.djangoproject.com/fr/2.1/ref/request-response/#passing-iterators # noqa
        content, url = open(data['path'], mode='rb'), data['url']

    filetype = magic.from_buffer(content.read(1024), mime=True)
    content.seek(0)

    if isinstance(permissions, list):
        if not set(permissions).intersection(
                request.user.get_all_permissions()):
            return HttpResponseForbidden()

    response = HttpResponse(content_type='application/octet-stream')
    if isinstance(headers, dict):
        for header, value in headers.items():
            response[header] = value

    if settings.MEDIA_ACCEL_REDIRECT:
        response['X-Accel-Redirect'] = f'{url}'
    else:
        response.content = content.read()
        response.content_type = filetype

    return response
