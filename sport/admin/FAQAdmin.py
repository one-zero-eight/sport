from django.contrib import admin
from django.contrib.auth.admin import GroupAdmin
from django.contrib.auth.models import Group as DjangoGroup
from sport.models import FAQElement, FAQCategory
from django.utils.html import format_html

from .site import site


@admin.register(FAQElement, site=site)
class FAQAdmin(admin.ModelAdmin):
    list_display = (
        'question',
        'formated_answer',
        'category',
    )

    list_filter = (
        "category",
    )

    def formated_answer(self, obj):
        return format_html(obj.answer)


@admin.register(FAQCategory, site=site)
class FAQAdmin(admin.ModelAdmin):
    list_display = (
        'name',
    )
