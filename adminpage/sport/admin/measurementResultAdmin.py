from django.contrib import admin

from sport.models import MeasurementResult


from .site import site


@admin.register(MeasurementResult, site=site)
class MeasurementResult(admin.ModelAdmin):
    list_display = (
        "student",
        "date",
        "semester",
        "measurement",
        "value"
    )

    def semester(self, object):
        return object.session.semester

    def date(self, object):
        return object.session.date

    def student(self, object):
        return object.session.student
