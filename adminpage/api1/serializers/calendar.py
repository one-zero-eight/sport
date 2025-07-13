from rest_framework import serializers


class CalendarRequestSerializer(serializers.Serializer):
    start = serializers.DateTimeField()
    end = serializers.DateTimeField()


class ScheduleExtendedPropsSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    group_id = serializers.IntegerField()
    training_class = serializers.CharField()
    current_load = serializers.IntegerField()
    capacity = serializers.IntegerField()


class CalendarSerializer(serializers.Serializer):
    title = serializers.CharField()
    start = serializers.DateTimeField()
    end = serializers.DateTimeField()
    extendedProps = ScheduleExtendedPropsSerializer()
