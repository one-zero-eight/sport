from django.urls import path, register_converter
from drf_spectacular.views import SpectacularSwaggerView, SpectacularJSONAPIView
from adminpage.settings import SPECTACULAR_SETTINGS_V2
from api_v2.views import (
    profile,
    group,
    training,
    attendance,
    calendar,
    reference,
    self_sport_report,
    fitness_test,
    semester,
    analytics,
    medical_groups,
    faq,
    student_statuses,
    training_classes,
    admin,
)

from drf_spectacular.utils import extend_schema, extend_schema_view
class NegativeIntConverter:
    regex = '-?[0-9]+'

    def to_python(self, value):
        return int(value)

    def to_url(self, value):
        return '%d' % value
register_converter(NegativeIntConverter, 'negint')

urlpatterns = [

    #for any user
    path(r"users/me", profile.get_user_info),
    path(r"users/me/schedule", calendar.get_personal_schedule),
    path(r"sports", group.sports_view),
    path(r"sports/<int:sport_id>/schedule", calendar.get_schedule),
    path(r"sport-groups/<int:group_id>", group.group_info_view),
    path(r"semesters", semester.get_semesters),
    path(r"semesters/<int:semester_id>", semester.get_semester_by_id),
    path(r"semesters/current", semester.get_current_semester),
    path(r"medical-groups", medical_groups.medical_groups_view),
    path(r"faq", faq.get_faq_dict),
    path(r"training-classes", training_classes.get_training_class_view),
    path(r"student-statuses", student_statuses.get_student_statuses),
    path(r"trainings/<int:training_id>", training.training_info),



    #for teacher
    path(r"fitness-test/exercises", fitness_test.get_exercises),
    path(r"fitness-test/sessions", fitness_test.get_sessions),
    path(r"fitness-test/sessions/<int:session_id>", fitness_test.fitness_test_session_view),
    path(r"fitness-test/suggest-student", fitness_test.suggest_fitness_test_student),
    path(r"trainings/<int:training_id>/attendance", attendance.training_attendance_view),
    path(r"trainings/<int:training_id>/attendance.csv", attendance.get_grades_csv),
    path(r"trainings/<int:training_id>/suggest-student", attendance.suggest_student),


    #for student
    path(r"students/<int:student_id>/semester-history", profile.get_student_all_semesters_history),
    path(r"students/<int:student_id>/semester-history/<int:semester_id>", profile.get_student_specific_semester_history),
    path(r"students/<int:student_id>/hours-summary", attendance.get_student_hours_summary),
    path(r"students/<int:student_id>/better-than", attendance.get_better_than_info),
    path(r"trainings/<int:training_id>/checkin", training.training_checkin_view),
    path(r"selfsport/types", self_sport_report.get_self_sport_types),
    path(r"selfsport/parse-strava", self_sport_report.get_strava_activity_info),
    path(r"selfsport/reports", self_sport_report.self_sport_reports),
    path(r"selfsport/reports/<int:report_id>", self_sport_report.get_selfsport_report_by_id),
    path(r"references/medical-leave", reference.reference_upload),
    path(r"references/medical-group", reference.medical_group_upload),


    #for admin
    path(r"users/<int:user_id>", admin.get_user_by_id),
    path(r"users/batch", admin.get_users_batch),
    
    # API Documentation
    path(
        "schema/",
        SpectacularJSONAPIView.as_view(custom_settings=SPECTACULAR_SETTINGS_V2),
        name="schema",
    ),
    path("docs", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger"),
]
