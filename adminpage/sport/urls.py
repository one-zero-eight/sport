from django.urls import path, re_path
from django.contrib.admin.views.decorators import staff_member_required
from django.views.generic import RedirectView

from .views import *

urlpatterns = [
    path('', login_redirect, name="login"),
    path('profile/', profile_view, name='profile'),
    path('analytics/', analytics_view, name='analytics'),
    # path('category/', category_view, name='category'),
    path('fitness_test/', fitness_test_view, name='fitness_test'),
    path('fitness_test/new', fitness_test_session_new_view,
         name='fitness_test_session_new'),
    path('fitness_test/<int:fitness_test_session_id>',
         fitness_test_session_view, name='fitness_test_session_old'),
    path(
        'calendar/sport/<int:sport_id>',
        calendar_view,
        name="sport_schedule_calendar"
    ),
    path(
        'calendar/extrasport',
        calendar_view_without_sport,
        name="extrasport_schedule_calendar"
    ),
    path(
        'form/meg_group',
        process_med_group_form,
        name="process_med_group_form"
    ),
    re_path(
        r'grafana/(?P<path>.*)$',
        staff_member_required(GrafanaProxyView.as_view()),
        name='grafana-dashboard'
    ),
    re_path(
        r'dashboard/(?P<path>.*)$',
        RedirectView.as_view(url="/grafana/dashboards"),
        name='redirect-to-grafana'
    ),
]
