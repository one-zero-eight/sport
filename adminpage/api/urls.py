from django.views.generic import RedirectView

from django.urls import path, re_path, register_converter
from drf_spectacular.views import SpectacularSwaggerView, SpectacularJSONAPIView, SpectacularYAMLAPIView

from api.views import (
    profile,
    enroll,
    group,
    training,
    attendance,
    calendar,
    reference,
    self_sport_report,
    fitness_test,
    measurement,
    semester,
    analytics,
    medical_groups,
)


class NegativeIntConverter:
    regex = '-?[0-9]+'

    def to_python(self, value):
        return int(value)

    def to_url(self, value):
        return '%d' % value
register_converter(NegativeIntConverter, 'negint')


urlpatterns = [
    # profile
    path(r"profile/student", profile.get_student_info),
    path(r"profile/change_gender", profile.change_gender),
    path(r"profile/QR/toggle", profile.toggle_QR_presence),
    path(r"profile/history/<int:semester_id>", profile.get_history),
    path(r"profile/history/by_date", attendance.get_student_trainings_between_dates),
    path(r"profile/history_with_self/<int:semester_id>", profile.get_history_with_self),

    # enroll
    path(r"enrollment/enroll", enroll.enroll),
    path(r"enrollment/unenroll", enroll.unenroll),
    path(r"enrollment/unenroll_by_trainer", enroll.unenroll_by_trainer),

    # group
    path(r"group/<int:group_id>", group.group_info_view),
    path(r"select_sport", group.select_sport),
    path(r"sports", group.sports_view),

    # training
    path(r"training/<int:training_id>", training.training_info),
    path(r"training/<int:training_id>/check_in", training.training_checkin),
    path(r"training/<int:training_id>/cancel_check_in", training.training_cancel_checkin),

    # attendance
    path(r"attendance/suggest_student", attendance.suggest_student),
    path(r"attendance/<int:training_id>/grades", attendance.get_grades),
    path(r"attendance/<int:training_id>/grades.csv", attendance.get_grades_csv),
    path(r"attendance/<int:group_id>/report",
         attendance.get_last_attended_dates),
    path(r"attendance/mark", attendance.mark_attendance),
    path(r"attendance/<int:student_id>/hours", attendance.get_student_hours_info),
    path(r"attendance/<int:student_id>/negative_hours", attendance.get_negative_hours_info),
    path(r"attendance/<int:student_id>/better_than", attendance.get_better_than_info),

    # calendar
    path(r"calendar/<negint:sport_id>/schedule", calendar.get_schedule),
    path(r"calendar/trainings", calendar.get_personal_schedule),

    # reference management
    path(r"reference/upload", reference.reference_upload),

    # self sport report
    path(r"selfsport/upload", self_sport_report.self_sport_upload),
    path(r"selfsport/types", self_sport_report.get_self_sport_types),
    path(r"selfsport/strava_parsing", self_sport_report.get_strava_activity_info),

    # fitness test
    path(r"fitnesstest/result", fitness_test.get_result),
    path(r"fitnesstest/upload", fitness_test.post_student_exercises_result),
    path(r"fitnesstest/upload/<int:session_id>", fitness_test.post_student_exercises_result),
    path(r"fitnesstest/exercises", fitness_test.get_exercises),
    path(r"fitnesstest/sessions", fitness_test.get_sessions),
    path(r"fitnesstest/sessions/<int:session_id>", fitness_test.get_session_info),
    path(r"fitnesstest/suggest_student", fitness_test.suggest_fitness_test_student),

    # measurement
    path(r"measurement/student_measurement", measurement.post_student_measurement),
    path(r"measurement/get_results", measurement.get_results),
    path(r"measurement/get_measurements", measurement.get_measurements),

    path(r"semester", semester.get_semester),

    # analytics
    path(r"analytics/attendance", analytics.attendance_analytics),

    # medical groups
    path(r"medical_groups/", medical_groups.medical_groups_view),
]

urlpatterns.extend([
    # OpenAPI schema & Swagger UI
    path('openapi.json', SpectacularJSONAPIView.as_view(), name='schema'),
    path('openapi.yaml', SpectacularYAMLAPIView.as_view(), name='schema-yaml'),
    path('docs', SpectacularSwaggerView.as_view(url_name='schema'), name='schema-swagger'),

    # Redirect from deprecated paths
    re_path(
        r'swagger(?P<format>\.json)$',
        RedirectView.as_view(url="/api/openapi.json"),
        name='redirect-to-schema'
    ),
    re_path(
        r'swagger(?P<format>\.yaml)$',
        RedirectView.as_view(url="/api/openapi.yaml"),
        name='redirect-to-schema-yaml'
    ),
    re_path(
        r'swagger/$',
        RedirectView.as_view(url="/api/docs"),
        name='redirect-to-schema-swagger'
    ),
    re_path(
        r'redoc/$',
        RedirectView.as_view(url="/api/docs"),
        name='redirect-to-schema-swagger-from-redoc'
    ),
])
