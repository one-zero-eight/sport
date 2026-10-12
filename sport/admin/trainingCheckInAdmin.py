from django.contrib import admin
from sport.models import TrainingCheckIn

from .site import site


@admin.register(TrainingCheckIn, site=site)
class TrainingCheckInAdmin(admin.ModelAdmin):
    autocomplete_fields = (
        "student",
        "training",
    )

    list_display = ('student', 'training')
    fields = ('student', "training")
