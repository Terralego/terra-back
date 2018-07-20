from django.db import models


class OdtFile(models.Model):
    name = models.CharField(max_length=50)
    odt = models.FileField(upload_to='odt-files/')
