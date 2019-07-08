import mimetypes
import os
import tempfile
import zipfile
from io import StringIO
from os.path import basename
from urllib.parse import urlparse

import weasyprint
from django.conf import settings
from django.contrib.staticfiles.finders import find
from django.core.files.storage import default_storage
from rest_framework import renderers

from .helpers import CustomCsvBuilder


class CSVRenderer(renderers.BaseRenderer):
    media_type = 'text/csv'
    format = 'csv'

    def render(self, data, media_type=None, renderer_context=None):
        csvbuilder = CustomCsvBuilder(data)
        csv_file = StringIO()

        csvbuilder.create_csv(csv_file)

        return csv_file.read()


def django_url_fetcher(url):
    mime_type, encoding = mimetypes.guess_type(url)
    url_path = urlparse(url).path
    data = {
        'mime_type': mime_type,
        'encoding': encoding,
        'filename': basename(url_path),
    }

    minio_scheme = 'https' if settings.AWS_S3_SECURE_URLS else 'http'
    minio_url_prefix = f"{minio_scheme}://{settings.AWS_S3_CUSTOM_DOMAIN}"

    if url.startswith(minio_url_prefix):  # media file from minio
        url = url.replace(
            minio_url_prefix,
            settings.AWS_S3_ENDPOINT_URL + settings.AWS_STORAGE_BUCKET_NAME
        )

    elif url_path.startswith(settings.MEDIA_URL):  # media file from filesystem
        path = url_path.replace(settings.MEDIA_URL, settings.MEDIA_ROOT)
        data['file_obj'] = default_storage.open(path)
        return data

    elif url_path.startswith(settings.STATIC_URL):
        path = url_path.replace(settings.STATIC_URL, '')
        data['file_obj'] = open(find(path), 'rb')
        return data

    # fall back to weasyprint default fetcher
    return weasyprint.default_url_fetcher(url)


class PdfRenderer(renderers.TemplateHTMLRenderer):
    media_type = 'application/pdf'
    format = 'pdf'

    def render(self, data, accepted_media_type=None, renderer_context=None):
        """Returns the rendered pdf"""
        html = super().render(data, accepted_media_type=accepted_media_type,
                              renderer_context=renderer_context)
        request = renderer_context['request']
        base_url = request.build_absolute_uri("/")

        kwargs = {}
        return weasyprint.HTML(
            string=html,
            base_url=base_url,
            url_fetcher=django_url_fetcher,
        ).write_pdf(**kwargs)


class ZipRenderer(renderers.BaseRenderer):
    media_type = 'application/zip'
    format = 'zip'

    def render(self, data, media_type=None, renderer_context=None):
        with tempfile.SpooledTemporaryFile() as tmp:
            with zipfile.ZipFile(tmp, 'w', zipfile.ZIP_DEFLATED) as archive:
                for file in data:
                    archive.writestr(
                        os.path.basename(file.name),
                        file.open().read(),
                    )
            tmp.seek(0)
            return tmp.read()
