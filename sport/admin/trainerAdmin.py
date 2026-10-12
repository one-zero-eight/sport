from django.contrib import admin

from sport.admin.utils import user__email
from sport.models import Trainer
from .site import site


@admin.register(Trainer, site=site)
class TrainerAdmin(admin.ModelAdmin):
    autocomplete_fields = (
        "user",
    )

    search_fields = (
        "user__first_name",
        "user__last_name",
        "user__email"
    )

    list_display = (
        "__str__",
        user__email,
    )

    ordering = (
        "user__first_name",
        "user__last_name"
    )

    list_select_related = (
        "user",
    )
