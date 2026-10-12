from django.contrib import admin

from sport.models import TrainingClass
from .site import site


@admin.register(TrainingClass, site=site)
class TrainingClassAdmin(admin.ModelAdmin):
    search_fields = (
        "name",
    )
