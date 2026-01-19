from rest_framework import serializers


class GenderSerializer(serializers.Serializer):
    student_id = serializers.IntegerField()
    gender = serializers.IntegerField(min_value=-1, max_value=1)


class TrainingHourSerializer(serializers.Serializer):
    group = serializers.CharField()
    timestamp = serializers.DateTimeField()
    hours = serializers.IntegerField()


class TrainingHistorySerializer(serializers.Serializer):
    training_id = serializers.IntegerField()
    date = serializers.CharField()
    time = serializers.CharField()
    hours = serializers.IntegerField()
    group_name = serializers.CharField()
    sport_name = serializers.CharField()
    training_class = serializers.CharField()
    custom_name = serializers.CharField()


class SemesterHistorySerializer(serializers.Serializer):
    semester_id = serializers.IntegerField()
    semester_name = serializers.CharField()
    semester_start = serializers.CharField()
    semester_end = serializers.CharField()
    required_hours = serializers.IntegerField()
    total_hours = serializers.IntegerField()
    trainings = TrainingHistorySerializer(many=True)


from api_v2.serializers.fitness_test import (
    FitnessTestSessionSerializer,
    FitnessTestStudentExerciseResult,
)


class FitnessTestStudentSessionResultSerializer(serializers.Serializer):
    session = FitnessTestSessionSerializer()
    exercise_results = FitnessTestStudentExerciseResult(many=True)


class StudentSpecificSemesterHistorySerializer(serializers.Serializer):
    semester_id = serializers.IntegerField()
    semester_name = serializers.CharField()
    trainings = TrainingHourSerializer(many=True)
    fitness_tests = FitnessTestStudentSessionResultSerializer(many=True)


class SemesterHistoryWithFitnessSerializer(SemesterHistorySerializer):
    fitness_tests = FitnessTestStudentSessionResultSerializer(many=True, required=False)
