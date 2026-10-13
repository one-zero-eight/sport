from django.contrib import admin

from sport.models import Measurement

from .admin_site import site


@admin.register(Measurement, site=site)
class Measurement(admin.ModelAdmin):
    list_display = ("name", "value_unit")
