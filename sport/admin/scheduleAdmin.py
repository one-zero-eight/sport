from django.contrib import admin

from sport.models import Schedule
from .inlines import ViewTrainingInline
from .utils import cache_filter, cache_dependent_filter, custom_order_filter, DefaultFilterMixIn, YourModelForm
from .site import site





@admin.register(Schedule, site=site)
class ScheduleAdmin(DefaultFilterMixIn):
    form = YourModelForm
    semester_filter = 'group__semester__id__exact'

    autocomplete_fields = (
        "group",
        "training_class"
    )

    search_fields = (
        "group__name",
    )

    ordering = (
        "weekday",
        "start",
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
        "weekday",
        "start",
        ("training_class", admin.RelatedOnlyFieldListFilter)
    )

    list_display = (
        "group",
        "weekday",
        "start",
        "end",
        "training_class",
    )

    fields = (
        "group",
        "weekday",
        "start",
        "duration",
        "training_class",
    )

    inlines = (
        ViewTrainingInline,
    )

    list_select_related = (
        "group__trainer",
        "group__semester",
        "training_class"
    )

    def get_readonly_fields(self, request, obj=None):
        """
        Make some-fields immutable once set
        """
        if obj is not None:
            return self.readonly_fields + ('group',)
        return self.readonly_fields

    class Media:
        js = (
            "sport/js/list_filter_collapse.js",
        )
