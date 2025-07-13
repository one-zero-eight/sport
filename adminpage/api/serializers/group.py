from rest_framework import serializers

from sport.models import Schedule


class ScheduleSerializer(serializers.Serializer):
    weekday = serializers.IntegerField()
    weekday_name = serializers.CharField()
    start_time = serializers.CharField()
    end_time = serializers.CharField()
    training_class = serializers.CharField(allow_null=True)


class SportEnrollSerializer(serializers.Serializer):
    sport_id = serializers.IntegerField()

class SportSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    name = serializers.CharField()
    special = serializers.BooleanField()

class SportsSerializer(serializers.Serializer):
    sports = serializers.ListField(child=SportSerializer())


class TrainerSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    name = serializers.CharField()
    email = serializers.EmailField()


class GroupInfoSerializer(serializers.Serializer):
    group_id = serializers.IntegerField()
    group_name = serializers.CharField()
    capacity = serializers.IntegerField()
    current_load = serializers.IntegerField()

    trainer_first_name = serializers.CharField()
    trainer_last_name = serializers.CharField()
    trainer_email = serializers.CharField()

    trainers = TrainerSerializer(many=True)

    is_enrolled = serializers.BooleanField()
    can_enroll = serializers.BooleanField()

    schedule = ScheduleSerializer(many=True)


class DetailedGroupSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    name = serializers.CharField()
    description = serializers.CharField()
    capacity = serializers.IntegerField()
    current_enrollment = serializers.IntegerField()
    free_places = serializers.IntegerField()
    is_club = serializers.BooleanField()
    accredited = serializers.BooleanField()
    is_enrolled = serializers.BooleanField()
    schedule = ScheduleSerializer(many=True)
    trainers = TrainerSerializer(many=True)
    allowed_medical_groups = serializers.ListField(child=serializers.CharField())


class DetailedSportSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    name = serializers.CharField()
    description = serializers.CharField()
    groups = DetailedGroupSerializer(many=True)
    total_groups = serializers.IntegerField()
    total_free_places = serializers.IntegerField()


class SportsWithGroupsSerializer(serializers.Serializer):
    sports = DetailedSportSerializer(many=True)
