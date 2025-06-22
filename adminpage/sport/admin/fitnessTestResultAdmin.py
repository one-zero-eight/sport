from django.contrib import admin
from sport.models import FitnessTestResult

from .site import site


@admin.register(FitnessTestResult, site=site)
class FitnessTestResultAdmin(admin.ModelAdmin):
    search_fields = (
        "student__user__first_name",
        "student__user__last_name",
        "student__user__email",
        "student__telegram",
    )

    autocomplete_fields = (
        "student",
    )

    list_display = (
        'student',
        'session',
        'exercise',
        'value',
    )

    def has_add_permission(self, request, obj=None):
        return False
