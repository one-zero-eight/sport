from django.contrib import admin

from api.crud import get_ongoing_semester
from sport.models import FitnessTestExercise, FitnessTestGrading

from .site import site

class FitnessTestExcerciseInline(admin.TabularInline):
    model = FitnessTestGrading
    extra = 0

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        print(db_field.name)
        if db_field.name == 'semester':
            kwargs['initial'] = get_ongoing_semester()
            return db_field.formfield(**kwargs)
        return super().formfield_for_foreignkey(
            db_field, request, **kwargs
        )


@admin.register(FitnessTestExercise, site=site)
class FitnessTestExerciseAdmin(admin.ModelAdmin):
    list_display = (
        '__str__',
        'value_unit',
        'threshold'
    )
    inlines = (FitnessTestExcerciseInline,)
