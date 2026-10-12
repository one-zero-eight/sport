from django.contrib import admin

from sport.models import SelfSportType
from .site import site


@admin.register(SelfSportType, site=site)
class SelfSportTypeAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'is_active',
        'pk',
    )

    fields = (
        ('name', 'is_active'),
        'application_rule',
    )

    list_filter = (
        'is_active',
    )
