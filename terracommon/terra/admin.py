from django.contrib.auth.models import Permission
from django.contrib.gis import admin

from . import models


@admin.register(models.Layer)
class LayerAdmin(admin.ModelAdmin):
    list_display = ('pk', 'name', 'group')
    list_filter = ('group', )


@admin.register(models.Feature)
class FeatureAdmin(admin.OSMGeoAdmin):
    list_display = ('pk', 'identifier', 'layer', 'source', 'target')
    list_filter = ('layer', )


admin.site.register(models.FeatureRelation)
admin.site.register(Permission)
