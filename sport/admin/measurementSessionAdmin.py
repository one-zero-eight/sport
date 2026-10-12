import datetime

from django.contrib import admin
from django.forms import BaseInlineFormSet

from api.crud import get_ongoing_semester
from .site import site
from sport.models import MeasurementSession, MeasurementResult, Measurement


class MeasurementResultInlineFormSet(BaseInlineFormSet):
    def __init__(self, *args, **kwargs):
        kwargs['initial'] = [{'measurement': e.id} for e in Measurement.objects.all()]
        super().__init__(*args, **kwargs)


class MeasurementResultInline(admin.TabularInline):
    model = MeasurementResult
    fields = ("measurement", "value")

    # TODO: get qty of measures
    max_num = 2
    extra = 2

    formset = MeasurementResultInlineFormSet


@admin.register(MeasurementSession, site=site)
class MeasurementSession(admin.ModelAdmin):
    autocomplete_fields = (
        "student",
    )

    list_display = (
        "student",
        "date",
        "semester",
        "approved"
    )

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        form.base_fields['approved'].initial = True
        return form

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == 'semester':
            kwargs['initial'] = get_ongoing_semester()
            return db_field.formfield(**kwargs)
        return super().formfield_for_foreignkey(
            db_field, request, **kwargs
        )

    inlines = (MeasurementResultInline, )
