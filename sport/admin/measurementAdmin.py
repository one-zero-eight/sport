from django.contrib import admin
from .site import site
from sport.models import Measurement


@admin.register(Measurement, site=site)
class Measurement(admin.ModelAdmin):
    list_display = (
        "name",
        "value_unit"
    )
