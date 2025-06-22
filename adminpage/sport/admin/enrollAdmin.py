from admin_auto_filters.filters import AutocompleteFilter
from django.contrib import admin

from sport.models import Enroll
from .site import site
from .utils import custom_titled_filter, cache_filter, \
    cache_dependent_filter, \
    custom_order_filter, DefaultFilterMixIn


class StudentTextFilter(AutocompleteFilter):
    title = "student"
    field_name = "student"
    parameter_name = "student"


# TODO: implement primary group export in grafana
# def export_primary_as_xlsx(modeladmin, request, queryset):
#     field_names = ["Group", "Fullname", "Email",
#                    "Monday", "Tuesday", "Wednesday",
#                    "Thursday", "Friday", "Saturday",
#                    "Sunday", ]
#     semester_id = request.GET.get("group__semester__id__exact")
#     work_book = Workbook(write_only=True)
#     if semester_id is None:
#         modeladmin.message_user(request, "Please filter by semester",
#         messages.ERROR)
#         return
#     else:
#         semester_name = Semester.objects.get(pk=semester_id).name
#
#     work_sheet = work_book.create_sheet(title=semester_name)
#     work_sheet.append(field_names)
#
#     for enrollment in queryset.select_related("group").order_by(
#     "group").prefetch_related("group__schedule"):
#         if not enrollment.is_primary:
#             continue
#         group = enrollment.group
#
#         schedule = [""] * 7
#         if group.schedule.exists():
#             for scheduled_training in group.schedule.all():
#                 schedule[scheduled_training.weekday] += f"{
#                 scheduled_training.start}-{scheduled_training.end}\n\n"
#
#         student_fullname = enrollment.student.user.get_full_name()
#         student_email = enrollment.student.user.email
#         data = [group.name, student_fullname, student_email, *schedule]
#
#         work_sheet.append(data)
#     with NamedTemporaryFile() as tmp:
#         work_book.save(tmp.name)
#         tmp.seek(0)
#         stream = tmp.read()
#
#     response = HttpResponse(
#         stream,
#         content_type='application/vnd.openxmlformats-officedocument
#         .spreadsheetml.sheet',
#     )
#     response['Content-Disposition'] = f'attachment;
#     filename=SportEnrollment_{semester_name}.xlsx'
#
#     return response


# export_primary_as_xlsx.short_description = "Export primary sport groups"


@admin.register(Enroll, site=site)
class EnrollAdmin(DefaultFilterMixIn):
    semester_filter = 'group__semester__id__exact'

    autocomplete_fields = (
        "student",
        "group",
    )

    list_filter = (
        StudentTextFilter,
        # semester filter, resets group sub filter
        (
            "group__semester",
            cache_filter(custom_order_filter(("-start",)), ["group__id"])
        ),
        # group filter, depends on chosen semester
        (
            "group",
            cache_dependent_filter({"group__semester": "semester"}, ("name",),
                                   select_related=["semester"])
        ),
        ("group__is_club", custom_titled_filter("club status")),
        ("group__sport", admin.RelatedOnlyFieldListFilter),
    )

    list_display = (
        'student',
        'group',
    )

    list_select_related = (
        "student",
        "student__user",
        "group",
        "group__semester",
    )

    class Media:
        pass
