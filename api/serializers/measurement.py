from rest_framework import serializers


class MeasurementSerializer(serializers.Serializer):
    name = serializers.CharField()
    value_unit = serializers.CharField()


class MeasurementPostSerializer(serializers.Serializer):
    student_id = serializers.IntegerField()
    measurement_id = serializers.IntegerField()
    value = serializers.IntegerField()


class MeasurementResultSerializer(serializers.Serializer):
    measurement = serializers.CharField()
    uint = serializers.CharField()
    value = serializers.IntegerField()
    approved = serializers.BooleanField()
    date = serializers.DateField()


class MeasurementResultsSerializer(serializers.Serializer):
    semester = serializers.CharField()
    result = MeasurementResultSerializer(many=True)
