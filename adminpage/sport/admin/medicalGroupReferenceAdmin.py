from admin_auto_filters.filters import AutocompleteFilter
from django import forms
from django.contrib import admin
from django.utils.html import format_html

from sport.admin import site
from sport.models import MedicalGroupReference, MedicalGroupReferenceImage, MedicalGroup, MedicalGroupHistory


class StudentTextFilter(AutocompleteFilter):
    title = "student"
    field_name = "student"


class MedicalGroupReferenceForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.student_id is not None:
            if MedicalGroupHistory.objects.filter(medical_group_reference=self.instance).exists():
                self.fields['medical_group'].initial = MedicalGroupHistory.objects.filter(medical_group_reference=self.instance).last().medical_group
            else:
                self.fields['medical_group'].initial = self.instance.student.medical_group_id

    medical_group = forms.ModelChoiceField(MedicalGroup.objects.all(), initial=-2)

    def clean_comment(self):
        if self.cleaned_data['medical_group'].pk == -2 and \
                self.cleaned_data['comment'] == '':
            raise forms.ValidationError('Please, specify reject reason in the comment field')
        return self.cleaned_data['comment']

    def save(self, commit=True):
        instance = super().save(commit)
        instance.student.medical_group_id = self.cleaned_data['medical_group'].pk
        instance.student.save()
        
        # FIXME: Подумать как сделать менее костыльно
        student_history = MedicalGroupHistory.objects.filter(student=instance.student)
        if student_history:
            last_med_hist = student_history.latest('changed')
            last_med_hist.medical_group_reference = instance
            last_med_hist.save()

        return instance

    class Meta:
        model = MedicalGroupReference
        fields = (
            'student',
            'comment'
        )


class MedicalGroupReferenceAdminImage(admin.TabularInline):
    model = MedicalGroupReferenceImage
    extra = 0


@admin.register(MedicalGroupReference, site=site)
class MedicalGroupReferenceAdmin(admin.ModelAdmin):
    form = MedicalGroupReferenceForm

    list_display = (
        "student",
        "resolved",
    )

    list_select_related = (
        "student",
        "student__user",
    )

    list_filter = (
        "resolved",
        StudentTextFilter,
    )

    fields = (
        ("student", "uploaded"),
        ("medical_group", "comment"),
        ("student_comment"),
    )

    readonly_fields = (
        "student",
        "uploaded",
        "student_comment",
    )

    inlines = (MedicalGroupReferenceAdminImage,)

    def save_model(self, request, obj, form, change):
        if obj.resolved is None or 'comment' in form.changed_data or 'medical_group' in form.changed_data:
            obj.resolved = form.cleaned_data['medical_group'].pk > -2
            super().save_model(request, obj, form, change)

    def has_add_permission(self, request):
        return False

    class Media:
        pass
