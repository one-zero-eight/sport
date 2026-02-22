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

