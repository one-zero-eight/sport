from django import forms
from django.contrib import admin
from django.contrib.admin.widgets import AdminDateWidget
from django.http import HttpRequest
from django.urls import reverse
from django.utils import timezone
from django.utils.safestring import mark_safe

from sport.models import Attendance, Schedule, Enroll, Group, Training, MedicalGroupHistory, TrainingCheckIn


class ViewMedicalGroupHistoryInline(admin.TabularInline):
    model = MedicalGroupHistory
    extra = 0
    fields = ("medical_group", "medical_group_reference_link", "changed")
    readonly_fields = fields

    def medical_group_reference_link(self, obj: MedicalGroupHistory):
        change_url = reverse('admin:sport_medicalgroupreference_change', args=(obj.medical_group_reference.pk,))
        return mark_safe('<a href="%s">%s</a>' % (change_url, obj.medical_group_reference))
    medical_group_reference_link.short_description = "medical group reference"

    def has_add_permission(self, request, obj):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    # def get_queryset(self, request):
    #     return super().get_queryset(request).filter(student=request.)


class ViewAttendanceInline(admin.TabularInline):
    model = Attendance
    extra = 0
    fields = ("training", "student", "hours")
    readonly_fields = ("training", "student")
    autocomplete_fields = ("training", "student")
    ordering = ("-training__start", "student__user__first_name", "student__user__last_name")

    def has_add_permission(self, request, obj):
        return False

    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            "training__group__semester",
            "student__user",
            "training__training_class"
        )


class AddAttendanceInline(ViewAttendanceInline):
    extra = 1
    verbose_name_plural = "Add extra attendance record"
    readonly_fields = ()

    def has_view_or_change_permission(self, request, obj=None):
        return False

    def has_add_permission(self, request, obj):
        return True


class HackAttendanceForm(forms.ModelForm):
    date = forms.DateField(
        label='Day',
        initial=timezone.now().date(),
        widget=AdminDateWidget(attrs={'size': 16})
    )

    class Meta:
        model = Attendance
        fields = ('hours',)


class HackAttendanceInline(ViewAttendanceInline):
    extra = 1
    verbose_name_plural = "Extra attendance records"
    readonly_fields = ()

    def has_view_or_change_permission(self, request, obj=None):
        return False

    def has_add_permission(self, request, obj):
        return True

    def has_delete_permission(self, request, obj=None):
        return False

    form = HackAttendanceForm
    fields = ('date', 'hours',)



class EnrollInline(admin.TabularInline):
    model = Enroll
    extra = 0
    autocomplete_fields = ("student",)
    ordering = ("student__user__first_name", "student__user__last_name")

    def has_change_permission(self, request, obj=None):
        return False

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("student__user", "group__semester")


class GroupInline(admin.TabularInline):
    model = Group
    extra = 0
    ordering = ("semester", "name")


class TrainingInline(admin.TabularInline):
    model = Training
    fields = ("start", "end", "training_class")
    autocomplete_fields = ("training_class",)
    extra = 0
    ordering = ("-start",)

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("training_class", "group__semester")


class ViewTrainingInline(TrainingInline):
    exclude = ("group",)
    extra = 0

    def has_add_permission(
            self, request: HttpRequest, *args, **kwargs
    ) -> bool:
        return False

class ViewTrainingCheckInInline(admin.TabularInline):
    model = TrainingCheckIn
    fields = ("date", "student")
    readonly_fields = ("date", )
    autocomplete_fields = ("student",)
    extra = 0

    def has_change_permission(self, request, obj=None):
        return False
