from django.contrib import admin

from api.crud import get_ongoing_semester
from sport.models import FitnessTestSession, FitnessTestResult

from .site import site

class FitnessTestResultInline(admin.TabularInline):
    model = FitnessTestResult

    fields = ("student", "exercise", "value")
    readonly_fields = ("student", "exercise")

    extra = 0

    def has_add_permission(self, request, obj):
        return False

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        print(db_field.name)
        if db_field.name == 'semester':
            kwargs['initial'] = get_ongoing_semester()
            return db_field.formfield(**kwargs)
        return super().formfield_for_foreignkey(
            db_field, request, **kwargs
        )


class AddFitnessTestResultInline(FitnessTestResultInline):
    extra = 4
    readonly_fields = ()
    autocomplete_fields = ("student", )

    def has_view_or_change_permission(self, request, obj=None):
        return False

    def has_add_permission(self, request, obj):
        return True


@admin.register(FitnessTestSession, site=site)
class FitnessTestSessionAdmin(admin.ModelAdmin):
    autocomplete_fields = (
        "teacher",
    )

    list_display = (
        'date',
        'teacher',
    )

    inlines = (FitnessTestResultInline, AddFitnessTestResultInline)
