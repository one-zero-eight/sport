import io
from collections import OrderedDict

from django.http import HttpResponseRedirect
from django.urls import path, reverse
from openpyxl import load_workbook

from django.conf import settings
from django.contrib import admin
from django import forms
from django.contrib.admin.widgets import AutocompleteSelectMultiple, AdminDateWidget, AutocompleteSelect
from django.db import transaction
from django.utils import timezone

import datetime
from api.crud import get_ongoing_semester, mark_hours
from sport.models import Training, Student, Group, Attendance
from .inlines import ViewAttendanceInline, AddAttendanceInline, HackAttendanceInline, ViewTrainingCheckInInline
from .utils import cache_filter, cache_dependent_filter, cache_alternative_filter, custom_order_filter, \
    DefaultFilterMixIn
from .site import site


class AutocompleteStudent:
    model = Student


class TrainingFormWithCSV(forms.ModelForm):
    attended_students = forms.ModelMultipleChoiceField(
        required=False,
        queryset=Student.objects.exclude(medical_group__name='Medical checkup not passed'),
        error_messages={'invalid_choice': 'The student has not passed medical check-up yet!'},
        widget=AutocompleteSelectMultiple(
            AutocompleteStudent,
            admin_site=site,
            attrs={'data-width': '50%'}
        ),
    )
    hours = forms.DecimalField(required=False, max_digits=5, decimal_places=2, min_value=0.01, max_value=999.99,
                               initial=1)
    xlsx = forms.FileField(required=False, widget=forms.FileInput(attrs={'accept': '.xlsx'}))

    def clean(self):
        cleaned_data = super().clean()
        attendances = []
        cleaned_data['attendances'] = attendances
        file = cleaned_data.get("xlsx", None)
        if file is None:
            return cleaned_data
        data = file.read()
        emails = []
        hours = {}
        ws = load_workbook(filename=io.BytesIO(data), read_only=True).active
        for i, row in enumerate(ws):
            if i == 0:
                if len(row) != 2:
                    raise forms.ValidationError(f"Expected 2 columns header, got {len(row)} columns")
                header = [row[0].value, row[1].value]
                if header != ["email", "hours"]:
                    raise forms.ValidationError(f"Missing header ['email', 'hours'], got: {header}")
                continue

            if len(row) != 2:
                raise forms.ValidationError(f"Expected 2 columns in each row, got {len(row)} columns in row {i + 1}")
            email, student_hours = row[0].value, row[1].value
            emails.append(email)
            try:
                hours[email] = round(float(student_hours), 2)
                assert 0 <= hours[email] < 1000  # TODO: hardcoded constant
            except (AssertionError, ValueError, TypeError):
                raise forms.ValidationError(
                    f"Got invalid hours value \"{student_hours}\" for email {email}, expected value in range [0,999.99]"
                )
        students = Student.objects.select_related('user').filter(user__email__in=emails)
        if len(students) != len(emails):
            missing = set(emails) - set(map(lambda student: student.user.email, students))
            raise forms.ValidationError(
                f"File contains {len(emails)} records. Only {len(students)} emails matched. "
                f"Missing students emails are: {', '.join(missing)}"
            )

        for student in students:
            attendances.append((student, hours[student.user.email]))


class ChangeTrainingForm(TrainingFormWithCSV):
    class Meta:
        model = Training
        fields = ('group', 'schedule', 'start', 'end', 'training_class')


class CreateExtraTrainingForm(TrainingFormWithCSV):
    event_name = forms.CharField(label='Event name', max_length=100, required=False)
    start_day = forms.DateField(
        label='Event start day',
        initial=timezone.now().date(),
        widget=AdminDateWidget(attrs={'size': 16})
    )
    end_day = forms.DateField(
        label='Event end day',
        required=False,
        widget=AdminDateWidget(attrs={'size': 16})
    )

    class Meta:
        model = Training
        fields = ('group', 'event_name', 'start_day', 'end_day')

    def save(self, commit=True):
        self.instance.start = datetime.datetime.combine(
            self.cleaned_data['start_day'],
            datetime.time(0, 0, 0),
            tzinfo=timezone.localtime().tzinfo
        )
        self.instance.end = datetime.datetime.combine(
            self.cleaned_data['start_day' if self.cleaned_data['end_day'] is None else 'end_day'],
            datetime.time(23, 59, 59),
            tzinfo=timezone.localtime().tzinfo
        )
        if len(self.cleaned_data['event_name']) > 0:
            self.instance.custom_name = self.cleaned_data['event_name']
        return super().save(commit)


CreateExtraTrainingForm.title = "Add extra training"


class MultiTrainingsForStudentForm(forms.ModelForm):
    student = forms.ModelChoiceField(
        Student.objects.exclude(medical_group__name='Medical checkup not passed'),
        error_messages={'invalid_choice': 'The student has not passed medical check-up yet!'},
        widget=AutocompleteSelect(Attendance._meta.get_field('student').remote_field, site),
    )

    class Meta:
        model = Training
        fields = ('group',)


MultiTrainingsForStudentForm.title = "Add multiple extra training records"


@admin.register(Training, site=site)
class TrainingAdmin(DefaultFilterMixIn):
    semester_filter = 'group__semester__id__exact'

    search_fields = (
        "group__name",
    )

    autocomplete_fields = (
        "group",
        "schedule",
        "training_class",
    )

    ordering = (
        '-start',
    )

    list_filter = (
        # semester filter, resets group sub filter
        (
            "group__semester",
            cache_filter(custom_order_filter(("-start",)), ["group__id"])
        ),
        # group filter, depends on chosen semester
        (
            "group",
            cache_dependent_filter({"group__semester": "semester"}, ("name",), select_related=["semester"])
        ),
        "group__sport",
        ("training_class", admin.RelatedOnlyFieldListFilter),
        ("start", cache_alternative_filter(admin.DateFieldListFilter, ["group__semester"])),
    )

    list_display = (
        "group",
        "custom_name",
        "start",
        "end",
        "training_class",
    )

    fields = (
        "group",
        "custom_name"
        "schedule",
        "start",
        "end",
        "training_class",
    )

    list_select_related = (
        "group__semester",
        "training_class",
    )

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('add-extra/', self.extra_add, name='sport_training_add_extra'),
            path('add-extra-multi/', self.extra_add_multi, name='sport_training_add_extra_multi'),
        ]
        return custom_urls + urls

    def extra_add(self, request):
        return self.changeform_view(request, None, '', None)

    def extra_add_multi(self, request):
        return self.changeform_view(request, None, '', {
            'show_save_and_continue': False
        })

    def get_form(self, request, obj=None, change=False, **kwargs):
        if 'add-extra-multi' in request.path:
            kwargs['form'] = MultiTrainingsForStudentForm
        elif 'add-extra' in request.path:
            kwargs['form'] = CreateExtraTrainingForm
        else:
            kwargs['form'] = ChangeTrainingForm
        return super().get_form(request, obj, change, **kwargs)

    def get_inlines(self, request, obj):
        if 'add-extra-multi' in request.path:
            return (
                HackAttendanceInline,
            )
        if obj is not None or 'add-extra' not in request.path:
            return (
                ViewAttendanceInline,
                AddAttendanceInline,
                ViewTrainingCheckInInline,
            )
        return (
            AddAttendanceInline,
        )

    def get_changeform_initial_data(self, request):
        """Custom form default values"""
        if 'add-extra-multi' in request.path:
            return {
                'group': Group.objects.get(semester=get_ongoing_semester(), name=settings.SELF_TRAINING_GROUP_NAME)
            }
        elif 'add-extra' in request.path:
            return {
                'group': Group.objects.get(semester=get_ongoing_semester(), name=settings.EXTRA_EVENTS_GROUP_NAME)
            }
        return {}

    def get_fieldsets(self, request, obj=None):
        if 'add-extra-multi' in request.path:
            return (
                (None, {
                    'fields': ('group', 'student', )
                }),
            )
        return (
            (None, {
                'fields': ('group', 'event_name', ('start_day', 'end_day'))
                if 'add-extra' in request.path
                else ('group', 'custom_name', 'start', 'end')
            }),
            ('Add attended students with same hours', {
                'fields': ('attended_students', 'hours',)
            }),
            ('Upload a xlsx file with attendance records', {
                'fields': ('xlsx',)
            }),
        )

    def save_model(self, request, obj, form, change):
        if 'add-extra-multi' in request.path:
            return None
        return super().save_model(request, obj, form, change)

    def construct_change_message(self, request, form, formsets, add=False):
        if 'add-extra-multi' in request.path:
            return None
        return super().construct_change_message(request, form, formsets, add)

    def log_addition(self, request, object, message):
        if 'add-extra-multi' in request.path:
            return None
        return super().log_addition(request, object, message)

    def response_add(self, request, obj, post_url_continue=None):
        if 'add-extra-multi' in request.path:
            obj_url = reverse(
                'admin:sport_training_changelist',
                current_app=site.name,
            )
            return HttpResponseRedirect(obj_url)
        return super().response_add(request, obj, post_url_continue)

    @transaction.atomic
    def save_related(self, request, form, formsets, change):
        """
        There are three ways of creating/changing attendance records (from highest priority to lowest):
        1) Upload CSV file
        2) Use ModelMultipleChoiceField in ModelAdmin for training
        3) Change/add attendance records using inline
        """
        if 'add-extra-multi' in request.path:
            for attendance_form in formsets[0].forms:
                attendance_form.instance.student = form.cleaned_data['student']
                start = datetime.datetime.combine(
                    datetime.date.fromisoformat(attendance_form['date'].value()),
                    datetime.time(0, 0, 0),
                    tzinfo=timezone.localtime().tzinfo
                )
                end = datetime.datetime.combine(
                    datetime.date.fromisoformat(attendance_form['date'].value()),
                    datetime.time(23, 59, 59),
                    tzinfo=timezone.localtime().tzinfo
                )
                training = Training.objects.create(group=form.instance.group, start=start, end=end)
                attendance_form.instance.training = training
                training.save(False)
                attendance_form.instance.save(False)
            return None
        super().save_related(request, form, formsets, change)
        training = form.instance
        similar_student_hours = [
            (student.pk, form.cleaned_data['hours'])
            for student in form.cleaned_data['attended_students']
        ]
        xlsx_student_hours = [
            (student.pk, hours)
            for (student, hours) in form.cleaned_data['attendances']
        ]
        mark_hours(training, OrderedDict(similar_student_hours + xlsx_student_hours).items())
        return training
