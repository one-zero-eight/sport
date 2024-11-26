from datetime import date, datetime
from tempfile import NamedTemporaryFile

from admin_auto_filters.filters import AutocompleteFilter
from django.conf import settings
from django.contrib import admin, messages
from django.db.models import Sum, Subquery, OuterRef
from django.db.models.functions import Coalesce
from django.http import HttpResponse
from django.urls import reverse
from django.utils.safestring import mark_safe
from openpyxl import Workbook
from rangefilter.filters import DateRangeFilter

from sport.admin.utils import cache_filter, cache_dependent_filter, custom_order_filter, DefaultFilterMixIn
from sport.models import Attendance, Student, Semester
from sport.utils import get_study_year_from_date
from .site import site


class StudentTextFilter(AutocompleteFilter):
    title = "student"
    field_name = "student"


def export_attendance_as_xlsx(modeladmin, request, queryset):
    """
    Exports attendance for a period given by semester and/or training__start range
    (the queryset must already be filtered !)
    """
    semester_id = request.GET.get("training__group__semester__id__exact", None)
    date_start_str = request.GET.get("training__start__range__gte", None)
    date_end_str = request.GET.get("training__start__range__lte", None)

    start = date.min
    end = date.max
    if semester_id is not None:
        semester = Semester.objects.get(id=semester_id)
        start = max(start, semester.start)
        end = min(end, semester.end)

    if date_start_str:
        start_date = datetime.strptime(date_start_str, settings.DATE_FORMAT).date()
        start = max(start, start_date)

    if date_end_str:
        end_date = datetime.strptime(date_end_str, settings.DATE_FORMAT).date()
        end = min(end, end_date)

    if start == date.min:
        modeladmin.message_user(
            request,
            "Please filter by semester or specify training start range",
            messages.ERROR,
        )
        return

    end = min(end, date.today())
    export_period = f"{start} - {end}"
    start_study_year = get_study_year_from_date(start)
    end_study_year = get_study_year_from_date(end)

    collected_hours = queryset.values("student_id").annotate(
        collected_hours=Sum('hours')
    ).filter(student_id=OuterRef("user_id")).values('collected_hours')

    student_data = Student.objects.filter(
        # suppose student enrolled in 2020-21 -> finish 4th course in 2023-24,
        # thus if start_study_year == 24 we exclude students enrolled in 2020
        enrollment_year__gt=start_study_year - settings.BACHELOR_STUDY_PERIOD_YEARS,
        # but include those enrolled in last study year
        enrollment_year__lte=end_study_year,
    ).annotate(
        collected_hours=Coalesce(Subquery(collected_hours), 0)
    ).select_related("user")

    wb = Workbook(write_only=True)
    ws = wb.create_sheet(export_period)
    ws.append(["Exported attendance for", export_period])
    ws.append(["enrollment_year", "course", "email", "hours"])
    for student in student_data:
        ws.append([student.enrollment_year, student.course, student.user.email, student.collected_hours])
    with NamedTemporaryFile() as tmp:
        wb.save(tmp.name)
        tmp.seek(0)
        stream = tmp.read()
    response = HttpResponse(
        stream,
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    )
    response['Content-Disposition'] = f'attachment; filename=SportHours_{export_period}.xlsx'

    return response


@admin.register(Attendance, site=site)
class AttendanceAdmin(DefaultFilterMixIn):
    semester_filter = 'training__group__semester__id__exact'
    # TODO: test performance
    # https://docs.djangoproject.com/en/3.0/ref/contrib/admin/#django.contrib.admin.ModelAdmin.autocomplete_fields
    autocomplete_fields = (
        "training",
        "student",
    )

    list_display = (
        "student",
        "training",
        "hours",
    )

    fields = (
        "student",
        "training",
        "hours",
        "cause_report_link",
        "cause_reference_link",
    )

    readonly_fields = (
        "cause_report_link",
        "cause_reference_link",
    )

    def cause_report_link(self, obj):
        change_url = reverse('admin:sport_selfsportreport_change', args=(obj.cause_report.pk,))
        return mark_safe('<a href="%s">%s</a>' % (change_url, obj.cause_report))

    cause_report_link.short_description = 'Self sport report'

    def cause_reference_link(self, obj):
        change_url = reverse('admin:sport_reference_change', args=(obj.cause_reference.pk,))
        return mark_safe('<a href="%s">%s</a>' % (change_url, obj.cause_reference))

    cause_reference_link.short_description = 'Medical leave reference'

    ordering = (
        "-training__start",
    )

    actions = (
        export_attendance_as_xlsx,
    )

    list_filter = (
        StudentTextFilter,
        ("training__start", DateRangeFilter),
        # semester filter, resets group sub filter
        (
            "training__group__semester",
            cache_filter(custom_order_filter(("-start",)), ["training__group__id"])
        ),
        # group filter, depends on chosen semester
        (
            "training__group",
            cache_dependent_filter({"training__group__semester": "semester__pk"}, ("name",),
                                   select_related=["semester"])
        ),
        "training__group__sport",
    )

    list_select_related = (
        "student__user",
        "training__group",
        "training__group__semester",
        "training__training_class",
    )

    class Media:
        pass
