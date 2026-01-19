from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from api_v2.serializers.semester import SemesterSerializer
from api_v2.serializers.student import UserSerializer
from sport.models import FitnessTestExercise, FitnessTestSession, FitnessTestResult


class FitnessTestExerciseSelectSerializer(serializers.ListSerializer):
    def to_internal_value(self, data):
        return ','.join(data)

    def to_representation(self, data):
        return data.split(',')


class FitnessTestExerciseSerializer(serializers.ModelSerializer[FitnessTestExercise]):
    name = serializers.CharField(source='exercise_name')
    unit = serializers.CharField(source='value_unit')
    select = FitnessTestExerciseSelectSerializer(child=serializers.CharField())

    class Meta:
        model = FitnessTestExercise
        fields = ('id', 'name', 'unit', 'threshold', 'select')


class FitnessTestResultSerializer(serializers.ModelSerializer[FitnessTestResult]):
    student = UserSerializer()

    class Meta:
        model = FitnessTestResult
        fields = ('student', 'value')


class FitnessTestResults(serializers.Serializer):
    result = FitnessTestResultSerializer(many=True)


class FitnessTestUpdateEntry(serializers.Serializer):
    student_id = serializers.IntegerField()
    exercise_id = serializers.IntegerField()
    value = serializers.CharField()


class FitnessTestUpload(serializers.Serializer):
    semester_id = serializers.IntegerField()
    retake = serializers.BooleanField()
    results = serializers.ListField(child=FitnessTestUpdateEntry())


class FitnessTestSessionSerializer(serializers.ModelSerializer[FitnessTestSession]):
    semester = SemesterSerializer()
    retake = serializers.BooleanField()
    teacher = serializers.CharField(source='teacher.__str__')  # TODO: return object

    class Meta:
        model = FitnessTestSession
        fields = ('id', 'semester', 'retake', 'date', 'teacher')


class FitnessTestSessionWithResult(serializers.Serializer):
    session = FitnessTestSessionSerializer()
    exercises = FitnessTestExerciseSerializer(many=True)
    results = serializers.DictField(child=FitnessTestResultSerializer(many=True))


class FitnessTestStudentExerciseResult(serializers.Serializer):
    exercise_id = serializers.IntegerField()
    exercise_name = serializers.CharField()
    unit = serializers.CharField(allow_null=True)
    value = serializers.CharField()


class FitnessTestStudentGroupedResult(serializers.Serializer):
    student = UserSerializer()
    exercise_results = FitnessTestStudentExerciseResult(many=True)


class FitnessTestSessionWithGroupedResults(serializers.Serializer):
    session = FitnessTestSessionSerializer()
    exercises = FitnessTestExerciseSerializer(many=True)
    results = serializers.DictField(child=FitnessTestStudentGroupedResult())
