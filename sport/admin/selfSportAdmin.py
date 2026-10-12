from admin_auto_filters.filters import AutocompleteFilter
from django import forms
from django.conf import settings
from django.db.models.functions import Coalesce
from django.urls import reverse
from django.utils.html import format_html
from django.utils.safestring import mark_safe

from django.db.models import F, Q, Sum, IntegerField, Case, When, OuterRef

from api.crud import get_ongoing_semester
from sport.models import SelfSportReport, Attendance
from .site import site
from .utils import custom_order_filter, DefaultFilterMixIn
import json
import logging

from django.contrib import admin

logger = logging.getLogger(__name__)


class StudentTextFilter(AutocompleteFilter):
    title = "student"
    field_name = "student"


def student__course(obj):
    return obj.student.course
student__course.short_description = 'course'


class ReferenceAcceptRejectForm(forms.ModelForm):
    def clean_comment(self):
        if self.cleaned_data['hours'] == 0 and self.cleaned_data['comment'] == '':
            raise forms.ValidationError('Please, specify reject reason in the comment field')
        return self.cleaned_data['comment']

    class Meta:
        model = SelfSportReport
        fields = (
            "student",
            "semester",
            "training_type",
            "hours",
            "comment",
            "link",
        )


@admin.register(SelfSportReport, site=site)
class SelfSportAdmin(DefaultFilterMixIn):
    semester_filter = 'semester__id__exact'

    form = ReferenceAcceptRejectForm

    list_display = (
        'student',
        student__course,
        'semester',
        'hours',
        'uploaded',
        'approval',
        "obtained_hours"
    )

    list_filter = (
        StudentTextFilter,
        ("semester", custom_order_filter(("-start",))),
        "approval",
        'student__course'
    )

    fields = (
        ("student", "uploaded"),
        "semester",
        "training_type",
        ("medical_group", "student_status"),
        ("hours", "obtained_self_hours", "obtained_hours"),
        ("parsed_data_json", "student_comment"),
        "comment",
        "link",
        # "reference_image",
        "attendance_link",
        "debt"
    )

    list_select_related = (
        'training_type',
    )

    readonly_fields = (
        "student",
        "uploaded",
        # "reference_image",
        "obtained_self_hours",
        'obtained_hours',
        'student_status',
        "attendance_link",
        "medical_group",
        "debt",
        "student_comment",
        "parsed_data_json"
    )

    def attendance_link(self, obj):
        change_url = reverse('admin:sport_attendance_change', args=(obj.attendance.pk,))
        return mark_safe('<a href="%s">%s</a>' % (change_url, obj.attendance))

    attendance_link.short_description = 'Attendance'

    autocomplete_fields = (
        "student",
    )

    def obtained_self_hours(self, obj: SelfSportReport):
        return Attendance.objects.filter(
            student=obj.student,
            training__group__semester=obj.semester,
            training__group__name=settings.SELF_TRAINING_GROUP_NAME,
        ).aggregate(
            Sum('hours')
        )['hours__sum']

    obtained_self_hours.short_description = "Self sport hours in semester"

    def obtained_hours(self, obj: SelfSportReport):
        return obj.obtained_hours

    obtained_hours.short_description = "All hours in semester"
    obtained_hours.admin_order_field = 'obtained_hours'

    def medical_group(self, obj: SelfSportReport):
        return obj.student.medical_group.name

    medical_group.short_description = "Student's medical group"

    def student_status(self, obj: SelfSportReport):
        return obj.student.student_status.name

    student_status.short_description = "Student status"

    def reference_image(self, obj):
        if obj.image is not None:
            return format_html(
                '<a href="{}"><img style="width: 50%" src="{}" /></a>',
                obj.image.url,
                obj.image.url
            )
        else:
            return "None"

    def save_model(self, request, obj, form, change):
        obj.approval = obj.hours > 0
        super().save_model(request, obj, form, change)

    reference_image.short_description = 'Reference'
    reference_image.allow_tags = True

    ordering = (F("approval").asc(nulls_first=True), "uploaded")

    def parsed_data_json(self, obj: SelfSportReport):
        return json.dumps(obj.parsed_data, indent=4)

    parsed_data_json.short_description = "Parsed data"

    def get_queryset(self, request):
        qs = super().get_queryset(request)

        attendance_query = (
            Attendance.objects.only('training__group__semester_id',
                                    'training__group__semester__hours',
                                    'student_id',
                                    'semester')
                # Get attendance, annotate, group by student and semester
                .annotate(semester=F("training__group__semester_id"),
                          semester_hours=F("training__group__semester__hours"))
                .values('semester', 'student_id').order_by('student_id', 'semester')
                # Calculate hours
                .annotate(sum_hours=Sum("hours", output_field=IntegerField()))
                .annotate(bounded_hours=Case(When(sum_hours__gt=F('semester_hours'),
                                                  then=F('semester_hours')),
                                             default=F('sum_hours')))
        )

        qs = qs.annotate(obtained_hours=Coalesce(
            attendance_query.filter(student_id=OuterRef("student__pk"), semester=get_ongoing_semester().pk).values('sum_hours'),
            0
        ))

        return qs

    class Media:
        pass
