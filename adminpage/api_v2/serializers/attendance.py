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



class TrainingGradesSerializer(serializers.Serializer):
    group_name = serializers.CharField()
    start = serializers.DateTimeField()
    grades = SuggestionSerializer(many=True)
    academic_duration = serializers.IntegerField()


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


class BetterThanInfoSerializer(serializers.Serializer):
    better_than = serializers.FloatField()


class StudentHoursSummarySerializer(serializers.Serializer):
    semester_id = serializers.FloatField(help_text="Current semester's id", required=False)
    debt = serializers.FloatField(help_text="Current student debt in hours", required=False)
    self_sport_hours = serializers.FloatField(help_text="Number of self sport hours", required=False)
    hours_from_groups = serializers.FloatField(help_text="Number of hours from sport groups", required=False)
    required_hours = serializers.FloatField(help_text="Number of hours required to achieve", required=False)
        
