from datetime import datetime

from django.db import models

date = datetime.now()


class DocumentTemplate(models.Model):
    name = models.CharField(max_length=50)
    template = models.FileField(upload_to=('template-'
                                           f'{date.month}-'
                                           f'{date.year}/'))
