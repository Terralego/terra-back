import csv
import io

from rest_framework.renderers import BaseRenderer


class CSVRenderer(BaseRenderer):
    media_type = 'text/plain'
    format = 'txt'

    def render(self, data, media_type=None, render_context=None):
        # TODO: do something with data -> into csv.
        # Use csv.DictWriter + io.BytesIO
        pass
