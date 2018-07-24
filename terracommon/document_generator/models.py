from django.db import models


class DocumentTemplate(models.Model):
    name = models.CharField(max_length=50)
    template = models.FileField(upload_to='templates/%Y/%m')
