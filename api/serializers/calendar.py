from rest_framework import serializers


class CalendarRequestSerializer(serializers.Serializer):
    start = serializers.DateTimeField()
    end = serializers.DateTimeField()


class ScheduleExtendedPropsSerializer(serializers.Serializer):
    id = serializers.IntegerField(required=False)
    group_id = serializers.IntegerField()
    training_class = serializers.CharField()
    current_load = serializers.IntegerField(required=False)
    capacity = serializers.IntegerField(required=False)
    is_paid = serializers.BooleanField()


class CalendarSerializer(serializers.Serializer):
    title = serializers.CharField()
    start = serializers.DateTimeField()
    end = serializers.DateTimeField()
    extendedProps = ScheduleExtendedPropsSerializer()
