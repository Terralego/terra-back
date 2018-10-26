
from io import StringIO

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
