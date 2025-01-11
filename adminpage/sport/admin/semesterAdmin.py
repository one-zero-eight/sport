from django.contrib import admin
from django.forms import ModelForm, CheckboxSelectMultiple, BooleanField

from sport.models import Semester
from .site import site
from .utils import copy_sport_groups_and_schedule_from_previous_semester


class SemesterAdminForm(ModelForm):
    copy_groups = BooleanField(required=False, label='Copy groups and schedule from previous semester')
    class Meta:
        model = Semester
        fields = '__all__'  # will be overridden by ModelAdmin
        widgets = {
            'nullify_groups': CheckboxSelectMultiple(),
            'participating_courses': CheckboxSelectMultiple()
        }


@admin.register(Semester, site=site)
class SemesterAdmin(admin.ModelAdmin):
    form = SemesterAdminForm
    search_fields = (
        "name",
        "start",
    )

    ordering = (
        "-start",
    )
    list_display = (
        "name",
        "start",
        "end",
        "hours",
        "points_fitness_test",
    )

    def save_model(self, request, obj, form, change):
        if form.cleaned_data.get('copy_groups', False) and not change:
            copy_sport_groups_and_schedule_from_previous_semester(obj)
        else:
            super().save_model(request, obj, form, change)

    def get_fields(self, request, obj=None):
        if obj is None:
            return (
                "name",
                "start",
                "end",
                "hours",
                "points_fitness_test",
                "academic_leave_students",
                "participating_courses",
                "number_hours_one_week_ill",
                "nullify_groups",
                "copy_groups",
                # "increase_course"
            )
        return (
            "name",
            "start",
            "end",
            "hours",
            "points_fitness_test",
            "academic_leave_students",
            "number_hours_one_week_ill",
            "participating_courses",
            "copy_groups",
        )

    autocomplete_fields = ('academic_leave_students',)
