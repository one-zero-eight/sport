from rest_framework import serializers


class EnrollSerializer(serializers.Serializer):
    group_id = serializers.IntegerField()


class UnenrollStudentSerializer(serializers.Serializer):
    group_id = serializers.IntegerField()
    student_id = serializers.IntegerField()
