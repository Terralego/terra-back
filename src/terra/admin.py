from django.contrib.gis import admin

from .models import Layer, Feature


admin.site.register(Layer)
admin.site.register(Feature, admin.OSMGeoAdmin)
