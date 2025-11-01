from django.urls import path, register_converter
from drf_spectacular.views import SpectacularSwaggerView, SpectacularJSONAPIView

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
)


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
    path(r"sports", group.clubs_view), # TODO: probably remove info about trainings
    path(r"sports/<int:sport_id>/schedule", calendar.get_schedule), # FIXME: returns []
    path(r"sport-groups/<int:group_id>", group.group_info_view),
    path(r"semesters", semester.get_semesters),
    path(r"semesters/<int:semester_id>", semester.get_semester_by_id),
    path(r"semesters/current", semester.get_current_semester),
    path(r"medical-groups", medical_groups.medical_groups_view),
    path(r"faq", faq.get_faq_dict),
    # path(r"locations", ),
    path(r"student-statuses", student_statuses.get_student_statuses),
    #for teacher
    
    
    #for student
    
    
    #for admin
    
    
    
    # profile
    #path(r"student/profile", profile.get_user_info),
    path(r"student/history/<int:semester_id>", profile.get_history_with_self),
    path(r"student/semester-history", profile.get_student_semester_history_view),

    # groups
    #path(r"sport-groups/<int:group_id>", group.group_info_view),
    #path(r"clubs", group.clubs_view),

    # trainings
    path(r"trainings/<int:training_id>", training.training_info),
    path(r"trainings/<int:training_id>/check-in", training.training_checkin),
    path(r"trainings/<int:training_id>/cancel-check-in", training.training_cancel_checkin),

    # attendance
    path(r"student/trainings", attendance.get_student_trainings_between_dates),
    path(r"attendance/students/search", attendance.suggest_student),
    path(r"trainings/<int:training_id>/grades", attendance.get_grades),
    path(r"trainings/<int:training_id>/grades.csv", attendance.get_grades_csv),
    path(r"groups/<int:group_id>/attendance-report", attendance.get_last_attended_dates),
    path(r"attendance/mark", attendance.mark_attendance),
    path(r"students/<int:student_id>/hours-summary", attendance.get_student_hours_summary),
    path(r"students/<int:student_id>/better-than", attendance.get_better_than_info),

    # calendar
    #path(r"sports/<negint:sport_id>/schedule", calendar.get_schedule),
    #path(r"student/schedule", calendar.get_personal_schedule),
    path(r"student/weekly-schedule", calendar.get_weekly_schedule_with_participants_view),

    # references
    path(r"references/upload", reference.reference_upload),

    # self sport report
    path(r"selfsport/upload", self_sport_report.self_sport_upload),
    path(r"selfsport/types", self_sport_report.get_self_sport_types),
    path(r"selfsport/strava_parsing", self_sport_report.get_strava_activity_info),

    # fitness tests
    path(r"fitness-test/result", fitness_test.get_result),
    path(r"fitness-test/upload", fitness_test.post_student_exercises_result),
    path(r"fitness-test/upload/<int:session_id>", fitness_test.post_student_exercises_result),
    path(r"fitness-test/exercises", fitness_test.get_exercises),
    path(r"fitness-test/sessions", fitness_test.get_sessions),
    path(r"fitness-test/sessions/<int:session_id>", fitness_test.get_session_info),
    path(r"fitness-test/students/search", fitness_test.suggest_fitness_test_student),

    #path(r"semester", semester.get_semesters),

    # analytics
    #path(r"analytics/attendance", analytics.attendance_analytics),

    # medical groups
    #path(r"medical-groups", medical_groups.medical_groups_view),

    # FAQ
    #path(r"faq", faq.get_faq_dict),

    # API Documentation
    path('schema/', SpectacularJSONAPIView.as_view(), name='schema'),
    path('docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger'),
]
