from admin_auto_filters.filters import AutocompleteFilter
from django.contrib import admin
from django.db.models import Model
from django.http import HttpRequest
from django.urls import reverse
from django.utils.html import format_html

from sport.models import MedicalGroupHistory

from .admin_site import site


class StudentTextFilter(AutocompleteFilter):
    title = "student"
    field_name = "student"


@admin.register(MedicalGroupHistory, site=site)
class MedicalGroupHistoryAdmin(admin.ModelAdmin):
    list_display = ("student", "medical_group", "changed")

    list_filter = (StudentTextFilter,)

    fields = ("student_link", "medical_group", "medical_group_reference_link", "changed")
    readonly_fields = fields

    def student_link(self, obj: MedicalGroupHistory):
        change_url = reverse("admin:sport_student_change", args=(obj.student.pk,))
        return format_html('<a href="{}">{}</a>', change_url, obj.student)

    student_link.short_description = "student"

    def medical_group_reference_link(self, obj: MedicalGroupHistory):
        change_url = reverse("admin:sport_medicalgroupreference_change", args=(obj.medical_group_reference.pk,))
        return format_html('<a href="{}">{}</a>', change_url, obj.medical_group_reference)

    medical_group_reference_link.short_description = "medical group reference"

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request: HttpRequest, obj: Model | None = None) -> bool:
        return False

    class Media:
        pass
