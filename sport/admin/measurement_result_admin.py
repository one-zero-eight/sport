from django.contrib import admin

from sport.models import MeasurementResult

from .admin_site import site


@admin.register(MeasurementResult, site=site)
class MeasurementResult(admin.ModelAdmin):
    list_display = ("student", "date", "semester", "measurement", "value")

    def semester(self, obj):
        return obj.session.semester

    def date(self, obj):
        return obj.session.date

    def student(self, obj):
        return obj.session.student
