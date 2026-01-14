from rest_framework import serializers
from django.utils import timezone
from django.conf import settings
from datetime import time




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

    # CRUD возвращает group_name -> маппим в title
    title = serializers.CharField(source="group_name")

    start = serializers.DateTimeField()
    end = serializers.DateTimeField()
    group_id = serializers.IntegerField()

    # В CRUD этого нет -> считаем в сериализере
    can_edit = serializers.SerializerMethodField()
    allDay = serializers.SerializerMethodField()

    can_grade = serializers.BooleanField()

    # В CRUD бывает None -> разрешаем null/blank
    training_class = serializers.CharField(allow_null=True, allow_blank=True, required=False)

    group_accredited = serializers.BooleanField()

    # В student CRUD есть, в trainer CRUD ты уже добавил тоже
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
