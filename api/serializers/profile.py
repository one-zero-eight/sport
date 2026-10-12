from rest_framework import serializers


class HasQRSerializer(serializers.Serializer):
    has_QR = serializers.BooleanField()


class GenderSerializer(serializers.Serializer):
    student_id = serializers.IntegerField()
    gender = serializers.IntegerField(min_value=-1, max_value=1)


class TrainingHourSerializer(serializers.Serializer):
    group = serializers.CharField()
    timestamp = serializers.DateTimeField()
    hours = serializers.IntegerField()
