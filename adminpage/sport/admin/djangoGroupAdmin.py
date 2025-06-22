from django.contrib import admin
from django.contrib.auth.admin import GroupAdmin
from django.contrib.auth.models import Group as DjangoGroup

from .site import site


@admin.register(DjangoGroup, site=site)
class DjangoGroupAdmin(GroupAdmin):
    list_display = (
        'verbose_name',
        'name',
    )
