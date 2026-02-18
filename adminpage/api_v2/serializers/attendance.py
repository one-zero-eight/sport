from rest_framework import serializers
from .medical_groups import (
    MedicalGroupSerializer,
)

class SuggestionQuerySerializer(serializers.Serializer):
    term = serializers.CharField()
    group_id = serializers.IntegerField()


class SuggestionQueryFTSerializer(serializers.Serializer):
    term = serializers.CharField()


class SuggestionSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    first_name = serializers.CharField()
    last_name = serializers.CharField()
    email = serializers.EmailField()
    medical_group = MedicalGroupSerializer()# serializers.CharField(allow_null=True, allow_blank=True)


class StudentInfoSerializer(serializers.Serializer):
    student_id = serializers.IntegerField()
    first_name = serializers.CharField()
    last_name = serializers.CharField()
    full_name = serializers.CharField()
    email = serializers.EmailField()


class GradeReportSerializer(StudentInfoSerializer):
    hours = serializers.IntegerField(default=None)


class TrainingGradesSerializer(serializers.Serializer):
    group_name = serializers.CharField()
    start = serializers.DateTimeField()
    grades = SuggestionSerializer(many=True)
    academic_duration = serializers.IntegerField()


class LastAttendedStat(StudentInfoSerializer):
    last_attended = serializers.CharField()


class LastAttendedDatesSerializer(serializers.Serializer):
    last_attended_dates = LastAttendedStat(many=True)


class BadGradeReportGradeSerializer(serializers.Serializer):
    email = serializers.EmailField()
    hours = serializers.IntegerField()


class BadGradeReport(serializers.Serializer):
    code = serializers.IntegerField()
    description = serializers.CharField()
    negative_marks = BadGradeReportGradeSerializer(many=True, default=None)
    overflow_marks = BadGradeReportGradeSerializer(many=True, default=None)


class GradeSetSerializer(serializers.Serializer):
    student_id = serializers.IntegerField()
    hours = serializers.IntegerField()


class AttendanceMarkSerializer(serializers.Serializer):
    training_id = serializers.IntegerField()
    students_hours = GradeSetSerializer(many=True)


class HourInfoSemesterChildSerializer(serializers.Serializer):
    id_sem = serializers.IntegerField()
    hours_not_self = serializers.IntegerField()
    hours_self_not_debt = serializers.IntegerField()
    hours_self_debt = serializers.IntegerField()
    hours_sem_max = serializers.IntegerField()
    debt = serializers.IntegerField()


class HoursInfoSerializer(serializers.Serializer):
    last_semesters_hours = HourInfoSemesterChildSerializer(many=True)
    ongoing_semester = HourInfoSemesterChildSerializer()


class HoursInfoFullSerializer(serializers.Serializer):
    final_hours = serializers.IntegerField()


class BetterThanInfoSerializer(serializers.Serializer):
    better_than = serializers.FloatField()


class AttendanceSerializer(serializers.Serializer):
    hours = serializers.IntegerField()
    training_id = serializers.IntegerField()
    date = serializers.DateField()
    training_class = serializers.CharField()
    group_id = serializers.IntegerField()
    group_name = serializers.CharField()
    trainers_emails = serializers.ListField()


class SemesterHoursSummarySerializer(serializers.Serializer):
    semester_id = serializers.IntegerField(help_text="Semester ID")
    semester_name = serializers.CharField(help_text="Semester name")
    debt = serializers.FloatField(help_text="Debt in hours for this semester")
    self_sport_hours = serializers.FloatField(help_text="Self sport hours for this semester")
    hours_from_groups = serializers.FloatField(help_text="Hours from sport groups for this semester")
    required_hours = serializers.FloatField(help_text="Required hours for this semester")
    is_current = serializers.BooleanField(help_text="Is this the current semester")


class StudentHoursSummarySerializer(serializers.Serializer):
    # Fields for current semester only (when current_semester_only=true)
    debt = serializers.FloatField(help_text="Current student debt in hours", required=False)
    self_sport_hours = serializers.FloatField(help_text="Number of self sport hours", required=False)
    hours_from_groups = serializers.FloatField(help_text="Number of hours from sport groups", required=False)
    required_hours = serializers.FloatField(help_text="Number of hours required to achieve", required=False)
    
    # Fields for all semesters (when current_semester_only=false)
    semesters = SemesterHoursSummarySerializer(many=True, help_text="List of semesters with hours info", required=False)
    
    # Common field
    current_semester_only = serializers.BooleanField(help_text="Current semester only or all semesters")


class GradesCsvRowSerializer(serializers.Serializer):
    student_id = serializers.IntegerField()
    full_name = serializers.CharField()
    email = serializers.EmailField()
    med_group = serializers.CharField(allow_null=True, required=False)
    hours = serializers.FloatField(allow_null=True, required=False)