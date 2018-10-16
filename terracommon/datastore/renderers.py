import csv
import io

from django.forms.models import model_to_dict
from rest_framework.renderers import BaseRenderer

from .models import DataStore


class CSVRenderer(BaseRenderer):
    media_type = 'text/plain'
    format = 'txt'

    def render(self, data, media_type=None, render_context=None):
        with open('fichier.csv', 'wb') as csvfile:
            writer = csv.writer(csvfile)

            for obj in DataStore.objects.all():
                row = ""

                for field in model_to_dict(obj):
                    row += getattr(obj, field) + ","

                writer.writerow(row)
