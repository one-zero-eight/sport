from django.contrib import admin
from django.contrib.auth import get_user_model
from hijack.contrib.admin import HijackUserAdminMixin
from django.db.models import ForeignKey, IntegerField, F, Sum
from django.db.models.expressions import Value, Case, When, Subquery, OuterRef, ExpressionWrapper
from django.db.models.functions import Coalesce, Least
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from import_export import resources, fields
from import_export.admin import ImportExportActionModelAdmin, ExportActionMixin
from import_export.results import RowResult
from import_export.widgets import ForeignKeyWidget

from api.crud import get_ongoing_semester, get_negative_hours, SumSubquery
from sport.models import Student, MedicalGroup, StudentStatus, Semester, Sport, Attendance, Debt, FitnessTestGrading, \
    FitnessTestResult, Enroll
from sport.signals import get_or_create_student_group
from .inlines import ViewAttendanceInline, AddAttendanceInline, ViewMedicalGroupHistoryInline
from .site import site
from .utils import user__role, DefaultFilterMixIn


class FitnessTestExcerciseInline(admin.TabularInline):
    model = FitnessTestResult
    extra = 0

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == 'semester':
            kwargs['initial'] = get_ongoing_semester()
            return db_field.formfield(**kwargs)
        return super().formfield_for_foreignkey(
            db_field, request, **kwargs
        )


class HoursFilter(admin.SimpleListFilter):
    title = 'hours'
    parameter_name = 'hours'

    def lookups(self, request, model_admin):
        return (
            ('less', 'Less -60'),
            ('-31', 'From -60 to -31'),
            ('-1', 'From -30 to -1'),
            ('29', 'From 0 to 29'),
            ('more', 'More 30')
        )

    def queryset(self, request, queryset):
        value = self.value()
        if value == 'less':
            return queryset.filter(hours__lt=-60)
        if value == '-31':
            return queryset.filter(hours__lt=-30).filter(hours__gte=-60)
        if value == '-1':
            return queryset.filter(hours__lt=0).filter(hours__gte=-30)
        if value == '29':
            return queryset.filter(hours__lt=30).filter(hours__gte=0)
        elif value == 'more':
            return queryset.filter(hours__gte=30)
        return queryset


class StudentResource(resources.ModelResource):
    medical_group = fields.Field(
        column_name="medical_group",
        attribute="medical_group",
        widget=ForeignKeyWidget(MedicalGroup, "name"),
    )

    student_status = fields.Field(
        column_name="student_status",
        attribute="student_status",
        widget=ForeignKeyWidget(StudentStatus, "name"),
    )

    sport = fields.Field(
        column_name="sport",
        attribute="sport",
        widget=ForeignKeyWidget(Sport, "name"),
    )

    hours = fields.Field(attribute='hours', readonly=True)

    def get_or_init_instance(self, instance_loader, row):
        student_group = get_or_create_student_group()
        user_model = get_user_model()
        user, _ = user_model.objects.get_or_create(
            email=row["email"],
            defaults={
                "first_name": row.get("first_name"),
                "last_name": row.get("last_name"),
            },
        )

        student_model_fields = [
            f.name
            for f in Student._meta.fields
            if not isinstance(f, ForeignKey)
        ]

        student_import_fields = row.keys() & student_model_fields

        student, student_created = Student.objects.get_or_create(
            user=user,
            defaults=dict([
                (key, row[key])
                for key in student_import_fields
            ])
        )
        if student_created:
            user.groups.add(student_group)

        return student, student_created

    class Meta:
        model = Student
        fields = (
            "user",
            "user__email",
            "user__first_name",
            "user__last_name",
            "enrollment_year",
            "course",
            "has_QR",
            "telegram",
            "is_online",
        )
        export_order = (
            "user",
            "user__email",
            "user__first_name",
            "user__last_name",
            "enrollment_year",
            "course",
            "has_QR",
            "medical_group",
            "student_status",
            "is_online",
            'sport',
            'hours',
            "telegram",
        )
        import_id_fields = ("user",)
        skip_unchanged = False
        report_skipped = True
        raise_errors = False

    def import_row(self, row, instance_loader, **kwargs):
        # overriding import_row to ignore errors and skip rows that fail to import
        # without failing the entire import
        import_result = super().import_row(row, instance_loader, **kwargs)
        if import_result.import_type == RowResult.IMPORT_TYPE_ERROR:
            # Copy the values to display in the preview report
            import_result.diff = [
                None,
                row.get('email'),
                row.get('first_name'),
                row.get('last_name'),
                row.get('medical_group'),
                row.get('enrollment_year'),
                row.get('course'),
                row.get('has_QR'),
                row.get('telegram'),
            ]
            # Add a column with the error message
            import_result.diff.append(mark_safe(
                f'''Errors:<ul>{''.join([f'<li>{err.error}</li>' for err in import_result.errors])}</ul>'''
            ))
            # clear errors and mark the record to skip
            import_result.errors = []
            import_result.import_type = RowResult.IMPORT_TYPE_SKIP

        return import_result


@admin.register(Student, site=site)
class StudentAdmin(HijackUserAdminMixin, ImportExportActionModelAdmin, DefaultFilterMixIn):
    default_filters = ['student_status__id__exact=0']
    resource_class = StudentResource

    def get_fields(self, request, obj=None):
        if obj is None:
            return (
                "user",
                "medical_group",
                "enrollment_year",
                "course",
                "student_status",
                "telegram",
            )
        return (
            "user",
            "gender",
            "has_QR",
            "is_online",
            "medical_group",
            "enrollment_year",
            "course",
            "sport",
            "student_status",
            "telegram" if obj.telegram is None or len(
                obj.telegram) == 0 else ("telegram", "write_to_telegram"),
            "comment",
        )

    autocomplete_fields = (
        "user",
    )

    search_fields = (
        "user__first_name",
        "user__last_name",
        "user__email",
        "telegram",
    )

    list_filter = (
        "course",
        "enrollment_year",
        "is_online",
        "medical_group",
        'student_status',
        'sport',
        'has_QR',
        HoursFilter
    )

    list_display = (
        "__str__",
        user__role,
        "has_QR",
        "is_online",
        "course",
        "medical_group",
        "sport",
        "hours",
        "student_status",
        "write_to_telegram",
    )

    readonly_fields = (
        "write_to_telegram",
    )

    def write_to_telegram(self, obj):
        return None if obj.telegram is None else \
            format_html(
                '<a target="_blank" href="https://t.me/{}">{}</a>',
                obj.telegram[1:],
                obj.telegram
            )

    def hours(self, obj: Student):
        return obj.hours
    hours.admin_order_field = 'hours'

    ordering = (
        "user__first_name",
        "user__last_name"
    )

    inlines = (
        ViewMedicalGroupHistoryInline,
        ViewAttendanceInline,
        AddAttendanceInline,
        FitnessTestExcerciseInline
    )

    # https://stackoverflow.com/a/66730984
    def change_view(self, request, object_id, form_url='', extra_context=None):
        try:
            obj = self.model.objects.get(pk=object_id)
        except self.model.DoesNotExist:
            pass
        else:
            if obj.medical_group.name == 'Medical checkup not passed':
                self.inlines = (ViewAttendanceInline,)
        return super().change_view(request, object_id, form_url, extra_context)


    def get_hijack_user(self, obj):
        return obj.user

    def delete_sport(self, request, queryset):
        queryset.update(sport=None)
        Enroll.objects.filter(student__in=queryset, group__semester=get_ongoing_semester()).delete()
    delete_sport.short_description = 'Deselect sport type and group'

    def increase_course(self, request, queryset):
        queryset.filter(student_status_id=0, course__gte=4).update(course=None, student_status_id=3)
        queryset.filter(student_status_id=0, course__lte=3).update(course=F('course') + 1)

    actions = [ExportActionMixin.export_admin_action, delete_sport, increase_course]

    list_select_related = (
        "user",
        "medical_group",
    )
