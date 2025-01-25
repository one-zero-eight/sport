from admin_auto_filters.filters import AutocompleteFilter
from django import forms
from django.contrib import admin
from django.db import ProgrammingError
from django.db.models.expressions import RawSQL
from django.forms import CheckboxSelectMultiple
from django.forms import ModelForm
from django.utils import timezone
from django.utils.html import format_html
from django.utils.safestring import mark_safe

from api.crud import get_ongoing_semester
from sport.models import Group, Semester
# from .inlines import EnrollInline, TrainingInline
from .site import site
from .utils import custom_titled_filter, DefaultFilterMixIn, ScheduleInline


def get_next_semester():
    try:
        next_sem = Semester.objects.filter(end__gt=timezone.now()).order_by("start").first()
        if not next_sem:
            return get_ongoing_semester()
        return next_sem
    except ProgrammingError:
        return get_ongoing_semester()


class ListTextWidget(forms.NumberInput):
    def __init__(self, data_list, name, *args, **kwargs):
        super(ListTextWidget, self).__init__(*args, **kwargs)
        self._name = name
        self._list = data_list

    def render(self, name, value, attrs=None, renderer=None):
        script = '<script>const clickButton = (name, value) => {' \
                 'document.getElementsByName(name)[0].value = value;' \
                 '}</script>'
        text_html = super(ListTextWidget, self).render(name, value, attrs=attrs)
        list_html = ''
        for e in self._list:
            list_html += '<button type="button" onclick="clickButton(\'%s\', \'%s\');">%s</button>' % (name, e, e)

        return mark_safe(script + '\n' + text_html + '\n' + list_html)


class TrainerTextFilter(AutocompleteFilter):
    title = "trainer"
    field_name = "trainers"


class GroupAdminForm(ModelForm):
    class Meta:
        model = Group
        fields = '__all__'  # will be overridden by ModelAdmin
        widgets = {
            'name': forms.TextInput(attrs={'size': '30', 'placeholder': 'Optional (e.g. Basic or Advanced)'}),
            'allowed_medical_groups': CheckboxSelectMultiple(),
            'capacity': ListTextWidget(data_list=(20, 25), name='capacity'),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['allowed_medical_groups'].initial = [2,1,0]

    def clean(self):
        cleaned_data = super().clean()
        sport = cleaned_data.get('sport')
        name = cleaned_data.get('name')
        if sport is None and name is None:
            self.add_error('sport', 'Sport or name must be specified')
            self.add_error('name', 'Sport or name must be specified')
        return super().clean()


@admin.register(Group, site=site)
class GroupAdmin(DefaultFilterMixIn):
    semester_filter = 'semester__id__exact', get_next_semester

    form = GroupAdminForm

    search_fields = (
        "name",
        "sport__name",
        "trainers__user__first_name",
        "trainers__user__last_name",
        "trainers__user__email",
    )

    autocomplete_fields = (
        "sport",
        # "trainer",
        'trainers',
        'allowed_students',
        'banned_students',
    )

    list_filter = (
        ("semester", admin.RelatedOnlyFieldListFilter),
        ("is_club", custom_titled_filter("club status")),
        TrainerTextFilter,
        ("sport", admin.RelatedOnlyFieldListFilter),
    )

    list_display = (
        "__str__",
        "is_club",
        "teachers",  # check function below
    )

    inlines = (
        ScheduleInline,
        # TrainingInline,
        # EnrollInline,
    )

    list_select_related = (
        "semester",
        "sport",
        "trainer__user",
    )

    fields = (
        "semester",
        "sport",
        "name",
        "is_club",
        "accredited",
        "capacity",
        "trainers",
        "allowed_medical_groups",
        "allowed_gender",
        "allowed_students",
        "banned_students",
    )

    def get_changeform_initial_data(self, request):
        return {'semester': get_next_semester()}

    readonly_fields = (
        "free_places",
    )

    # filter_horizontal = ('trainers',)

    def teachers(self, obj):
        return format_html(";<br>".join([t.user.first_name + ' ' + t.user.last_name for t in obj.trainers.all()]))

    def free_places(self, obj):
        return obj.capacity - obj.enroll_count

    def accredit(self, request, queryset):
        queryset.update(accredited=True)

    actions = [accredit]

    # Dirty hack, filter autocomplete groups in "add extra form"
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if 'extra' in request.META.get('HTTP_REFERER', []):
            return qs.filter(semester=get_ongoing_semester(), sport=None).order_by('name')
        return qs.annotate(enroll_count=RawSQL('select count(*) from enroll where group_id = "group".id', ()))
