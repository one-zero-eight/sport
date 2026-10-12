from admin_auto_filters.filters import AutocompleteFilter
from django import forms
from django.contrib import admin
from django.db.models import F
from django.urls import reverse
from django.utils.html import format_html
from django.utils.safestring import mark_safe

from sport.admin.utils import custom_order_filter, DefaultFilterMixIn
from sport.models import Reference
from .site import site


class StudentTextFilter(AutocompleteFilter):
    title = "student"
    field_name = "student"


class ReferenceAcceptRejectForm(forms.ModelForm):
    def clean_comment(self):
        if self.cleaned_data['hours'] == 0 and self.cleaned_data['comment'] == '':
            raise forms.ValidationError('Please, specify reject reason in the comment field')
        return self.cleaned_data['comment']

    class Meta:
        model = Reference
        fields = (
            "student",
            "semester",
            "hours",
            "comment"
        )



@admin.register(Reference, site=site)
class ReferenceAdmin(DefaultFilterMixIn):
    semester_filter = 'semester__id__exact'

    form = ReferenceAcceptRejectForm

    list_display = (
        "student",
        "semester",
        "image",
        "uploaded",
        "approval",
        "hours",
    )

    list_filter = (
        StudentTextFilter,
        ("semester", custom_order_filter(("-start",))),
        "approval"
    )

    fields = (
        "student",
        "semester",
        ("start", "end"),
        "uploaded",
        "hours",
        "student_comment",
        "comment",
        "reference_image",
        "attendance_link"
    )

    readonly_fields = (
        "student",
        "semester",
        "uploaded",
        "reference_image",
        "attendance_link",
        "student_comment"
    )

    def attendance_link(self, obj):
        change_url = reverse('admin:sport_attendance_change', args=(obj.attendance.pk,))
        return mark_safe('<a href="%s">%s</a>' % (change_url, obj.attendance))

    attendance_link.short_description = 'Attendance'

    autocomplete_fields = (
        "student",
    )

    ordering = (F("approval").asc(nulls_first=True), "uploaded")

    def reference_image(self, obj):
        return format_html(
            '<a href="{}"><img style="width: 50%" src="{}" /></a>',
            obj.image.url,
            obj.image.url
        )

    reference_image.short_description = 'Reference'
    reference_image.allow_tags = True

    class Media:
        pass
