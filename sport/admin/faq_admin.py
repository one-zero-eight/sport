from django.contrib import admin
from django.utils.html import format_html

from sport.models import FAQCategory, FAQElement

from .admin_site import site


@admin.register(FAQElement, site=site)
class FAQAdmin(admin.ModelAdmin):
    list_display = (
        "question",
        "formated_answer",
        "category",
    )

    list_filter = ("category",)

    def formated_answer(self, obj):
        return format_html(obj.answer)


@admin.register(FAQCategory, site=site)
class FAQCategoryAdmin(admin.ModelAdmin):
    list_display = ("name",)
