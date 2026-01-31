from rest_framework import serializers
from django.utils import timezone
from django.conf import settings
from datetime import time
from datetime import datetime




class CalendarRequestSerializer(serializers.Serializer):
    start = serializers.DateTimeField()
    end = serializers.DateTimeField()
    def validate(self, attrs):
        if not isinstance(attrs["start"], datetime):
            raise serializers.ValidationError("start_date must be datetime")
        if not isinstance(attrs["end"], datetime):
            raise serializers.ValidationError("end_date must be datetime")
        if attrs["start"] >= attrs["end"]:
            temp = attrs["start"]
            attrs["start"] = attrs["end"]
            attrs["end"] = temp
        return attrs


class ScheduleExtendedPropsSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    group_id = serializers.IntegerField()
    training_class = serializers.CharField()
    current_load = serializers.IntegerField()
    capacity = serializers.IntegerField()


class CalendarSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    title = serializers.CharField()
    start = serializers.DateTimeField()
    end = serializers.DateTimeField()
    group_id = serializers.IntegerField()
    training_class = serializers.CharField()
    current_load = serializers.IntegerField()
    capacity = serializers.IntegerField()
    # extendedProps = ScheduleExtendedPropsSerializer()

class CalendarPersonalSerializer(serializers.Serializer):
    id = serializers.IntegerField()

    title = serializers.CharField(source="group_name")

    start = serializers.DateTimeField()
    end = serializers.DateTimeField()
    group_id = serializers.IntegerField()

    can_edit = serializers.SerializerMethodField()
    allDay = serializers.SerializerMethodField()

    can_grade = serializers.BooleanField()

    training_class = serializers.CharField(allow_null=True, allow_blank=True, required=False)

    group_accredited = serializers.BooleanField()

    can_check_in = serializers.BooleanField(required=False, default=False)
    checked_in = serializers.BooleanField(required=False, default=False)

    def get_can_edit(self, obj):
        start_time = timezone.localtime(obj["start"])
        now = timezone.localtime()
        return start_time <= now <= start_time + settings.TRAINING_EDITABLE_INTERVAL

    def get_allDay(self, obj):
        start_time = timezone.localtime(obj["start"])
        end_time = timezone.localtime(obj["end"])
        return (
            start_time.time() == time(0, 0, 0)
            and end_time.time() == time(23, 59, 59)
        )

class CalendarSportSerializer(serializers.Serializer):
    title = serializers.CharField()
    daysOfWeek = serializers.ListField(child=serializers.IntegerField())
    startTime = serializers.TimeField()
    endTime = serializers.TimeField()
    group_id = serializers.IntegerField()
    training_class = serializers.CharField()
    current_load = serializers.IntegerField()
    capacity = serializers.IntegerField()

class ScheduleSportSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    start = serializers.DateTimeField()
    end = serializers.DateTimeField()
    group_id = serializers.IntegerField(source="group__id")
    group_name = serializers.CharField()
    sport_id = serializers.IntegerField(source="group__sport__id")
    sport_name = serializers.CharField()
    training_class_id = serializers.IntegerField(source="training_class__id")
    training_class = serializers.CharField(source="training_class__name")
    group_capacity = serializers.IntegerField()
    is_club = serializers.BooleanField()




class TrainingParticipantSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    name = serializers.CharField()
    email = serializers.EmailField()
    medical_group = serializers.CharField(allow_null=True)
    hours = serializers.FloatField()
    attended = serializers.BooleanField()


class TrainingParticipantsInfoSerializer(serializers.Serializer):
    total_checked_in = serializers.IntegerField()
    students = TrainingParticipantSerializer(many=True)


class WeeklyTrainingSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    start = serializers.DateTimeField()
    end = serializers.DateTimeField()
    group_id = serializers.IntegerField()
    group_name = serializers.CharField()
    training_class = serializers.CharField(allow_null=True)
    group_accredited = serializers.BooleanField()
    can_grade = serializers.BooleanField()
    can_check_in = serializers.BooleanField()
    checked_in = serializers.BooleanField()
    capacity = serializers.IntegerField()
    available_spots = serializers.IntegerField()
    participants = TrainingParticipantsInfoSerializer()


class WeeklyScheduleSerializer(serializers.Serializer):
    trainings = WeeklyTrainingSerializer(many=True)
