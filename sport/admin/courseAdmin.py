from django.contrib import admin

from sport.models import Course
from .site import site


@admin.register(Course, site=site)
class CourseAdmin(admin.ModelAdmin):
    autocomplete_fields = ('curator',)
    list_display = ('course', 'curator')
    list_select_related = ('curator__user',)
