import operator
from typing import List, Dict, Tuple

from django.contrib import admin
from django.contrib.admin.widgets import AdminTimeWidget
from django.db.models.expressions import F
from django.urls import reverse
from django.utils.translation import gettext_lazy as _


from django import forms
import datetime

from api.crud import get_ongoing_semester
from sport.models import Schedule, Semester, Group
from adminpage.settings import NOT_COPYABLE_GROUPS


class DurationWidget(forms.TimeInput):
    class Media:
        js = [
            'admin/js/calendar.js',
            'admin/js/admin/DateTimeShortcuts.js',
        ]

    def __init__(self, attrs=None, format=None):
        attrs = {'class': 'vDurationField', 'size': '8', 'data-format': format, 'data-mask': "99:99:99", **(attrs or {})}
        super().__init__(attrs=attrs, format=format)


class TimeWidget(AdminTimeWidget):
    def __init__(self, attrs=None, format=None):
        attrs = {'data-mask': "99:99:99", **(attrs or {})}
        super().__init__(attrs=attrs, format=format)


class YourModelForm(forms.ModelForm):
    duration = forms.DurationField(widget=DurationWidget(format='%H:%M:%S'), required=True)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.pk is not None:
            self.fields['duration'].initial = datetime.datetime.combine(datetime.date.today(), self.instance.end) - \
                                              datetime.datetime.combine(datetime.date.today(), self.instance.start)
        else:
            self.fields['duration'].initial = datetime.timedelta(hours=1, minutes=30)

    def save(self, commit=True):
        duration = self.cleaned_data.get('duration', None)
        self.instance.end = (datetime.datetime.combine(datetime.date.today(), self.instance.start) + duration).time()
        return super(YourModelForm, self).save(commit=commit)

    class Meta:
        model = Schedule
        # fields = '__all__'  # will be overridden by ModelAdmin
        widgets = {
            'start': TimeWidget(),
        }
        exclude = ('end',)


class ScheduleInline(admin.TabularInline):
    model = Schedule
    form = YourModelForm
    fields = ('weekday', 'start', 'duration', "training_class")

    extra = 0
    min_num = 1
    ordering = ("weekday", "start")
    autocomplete_fields = ("training_class",)

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("group__semester", "training_class")

class DefaultFilterMixIn(admin.ModelAdmin):
    def changelist_view(self, request, *args, **kwargs):
        from django.http import HttpResponseRedirect
        if hasattr(self, 'semester_filter') and self.semester_filter:
            if not isinstance(self.semester_filter, tuple):
                self.semester_filter = (self.semester_filter, get_ongoing_semester)
            filter = F'{self.semester_filter[0]}={self.semester_filter[1]().pk}'
            if hasattr(self, 'default_filters') and self.default_filters:
                self.default_filters.append(filter)
            else:
                self.default_filters = [filter]
        if hasattr(self, 'default_filters') and self.default_filters:
            try:
                test = request.META['HTTP_REFERER'].split(request.META['PATH_INFO'])
                if test and test[-1] and not test[-1].startswith('?'):
                    url = reverse('admin:%s_%s_changelist' % (self.opts.app_label, self.opts.model_name))
                    filters = []
                    for filter in self.default_filters:
                        key = filter.split('=')[0]
                        if key not in request.GET:
                            filters.append(filter)
                    if filters:
                        return HttpResponseRedirect("%s?%s" % (url, "&".join(filters)))
            except:
                pass
        return super(DefaultFilterMixIn, self).changelist_view(request, *args, **kwargs)


def user__email(obj):
    return obj.user.email


user__email.short_description = 'user email'


def user__role(obj):
    return obj.user.role


user__role.short_description = 'group'


def custom_order_filter(ordering: Tuple, cls=admin.RelatedFieldListFilter):
    class Wrapper(cls):
        def field_admin_ordering(self, field, request, model_admin):
            return ordering

    return Wrapper


def custom_titled_filter(title, filter_class=admin.RelatedFieldListFilter):
    class Wrapper(filter_class):
        def __new__(cls, *args, **kwargs):
            instance = filter_class.create(*args, **kwargs)
            instance.title = title
            return instance

    return Wrapper


def cache_filter(cls, clear_list: List[str]):
    """
    Overrides filter methods, so that chosen filter value will be available to other filters
    @param cls: used filter class
    @param clear_list: list of query fields that should be cleared, when some choice within this filter is selected.
    Useful for clearing dependent sub filters (clear semester choice, when study year is selected).
    """

    def add_value_to_cache(request, param, value):
        try:
            request.cache_filter[param] = value
        except:
            request.cache_filter = {param: value}

    class CacheAwareFilter(cls):
        def lookups(self, request, model_admin):
            add_value_to_cache(request, self.parameter_name, self.value())
            return super().lookups(request, model_admin)

        def field_choices(self, field, request, model_admin):
            add_value_to_cache(request, self.field_path, self.lookup_val)
            return super().field_choices(field, request, model_admin)

        def has_output(self):
            return True

        def choices(self, changelist):
            # save previous version of get_query_string that is used in super().choices(changelist)
            f = changelist.get_query_string

            def get_query_string(new_params=None, remove=None):
                # call prior version with additional 'remove' fields
                if remove is None:
                    return f(new_params=new_params, remove=clear_list)
                if isinstance(remove, dict):
                    remove = [key for key in remove]
                return f(new_params=new_params, remove=clear_list + remove)

            # override get_query_string
            changelist.get_query_string = get_query_string
            yield from super().choices(changelist)
            # revert to original get_query_string, since it can be used further
            changelist.get_query_string = f

    return CacheAwareFilter


def cache_dependent_filter(translation: Dict[str, str], order=None, select_related: List[str] = None):
    """
    Creates foreign key list filter, that can use cached values from other filters
    @param translation: rules for translating cached keys, if 'key' is cached,
    @param order: desired filter list ordering
    @param select_related: related fields for faster lookup in one sql query
    translation['key'] will be used as the actual filter parameter
    """

    class CacheRelatedFieldListFilter(admin.RelatedFieldListFilter):
        def field_choices(self, field, request, model_admin):
            self.no_output = any(map(lambda x: request.cache_filter[x] is None, translation))
            if self.no_output:
                return []
            additional_filter = {translation[k]: int(request.cache_filter[k][0]) for k in translation}
            ordering = order or self.field_admin_ordering(field, request, model_admin)

            # adapted from field.get_choices(...)
            if field.choices is not None:
                return list(field.choices)
            rel_model = field.remote_field.model
            choice_func = operator.attrgetter(
                field.remote_field.get_related_field().attname
                if hasattr(field.remote_field, 'get_related_field')
                else 'pk'
            )
            qs = rel_model._default_manager.complex_filter(additional_filter).order_by(*ordering)
            if select_related is not None:
                qs = qs.select_related(*select_related)
            return [
                (choice_func(x), str(x)) for x in qs
            ]

        def has_output(self):
            return not self.no_output

    return CacheRelatedFieldListFilter


def cache_alternative_filter(cls, cache_keys: List[str]):
    """
    Creates foreign key list filter, that will be used when one of the cache value is empty
    @param cache_keys: used cached keys, if an associated value for some given 'key' is None,
    filter will be rendered
    """

    class CacheRelatedFieldListFilter(cls):
        def __init__(self, field, request, *args, **kwargs):
            self.no_output = any(map(lambda x: request.cache_filter[x] is None, cache_keys))
            super().__init__(field, request, *args, **kwargs)

        def has_output(self):
            return self.no_output

    return CacheRelatedFieldListFilter


def has_free_places_filter():
    class Wrapper(admin.SimpleListFilter):
        title = 'free places'
        parameter_name = 'has_free_places'

        def lookups(self, request, model_admin):
            return (
                ('1', _('Has free places')),
                ('0', _('Group is full')),
            )

        def queryset(self, request, queryset):
            # enroll_count field was added using qs.annotate, see get_queryset() in groupAdmin
            if self.value() == '1':
                return queryset.filter(capacity__gt=F('enroll_count'))
            if self.value() == '0':
                return queryset.filter(capacity__lte=F('enroll_count'))
            return queryset

    return Wrapper


def copy_sport_groups_and_schedule_from_previous_semester(semester: Semester) -> None:
    semester.save()
    prev_semester = Semester.objects.filter(start__lt=semester.start).order_by('-start').first()
    sport_groups = Group.objects.filter(semester__pk=prev_semester.pk).prefetch_related('trainers', 'allowed_medical_groups', 'schedule').select_related('trainer').order_by('pk')
    new_sport_groups = []
    for group in sport_groups:
        if group.name in NOT_COPYABLE_GROUPS:
            continue
        new_group = Group(
            semester=semester,
            sport=group.sport,
            name=group.name,
            capacity=group.capacity,
            is_club=group.is_club,
            trainer=group.trainer,
            accredited=group.accredited,
            allowed_gender=group.allowed_gender,
            allowed_qr=group.allowed_qr,
        )
        new_sport_groups.append(new_group)
    Group.objects.bulk_create(new_sport_groups)

    new_sport_groups = Group.objects.filter(semester__pk=semester.pk).order_by('pk')
    for old_group, new_group in zip(sport_groups, new_sport_groups):
        for trainer in old_group.trainers.all():
            new_group.trainers.add(trainer)
        for medical_group in old_group.allowed_medical_groups.all():
            new_group.allowed_medical_groups.add(medical_group)
        for schedule_obj in old_group.schedule.all():
            new_group.schedule.add(schedule_obj)
