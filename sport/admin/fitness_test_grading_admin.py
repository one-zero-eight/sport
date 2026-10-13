from django.contrib import admin

from sport.models import FitnessTestGrading

from .admin_site import site


@admin.register(FitnessTestGrading, site=site)
class FitnessTestGradingAdmin(admin.ModelAdmin):
    list_display = ("exercise", "gender", "score", "start_range", "end_range")
