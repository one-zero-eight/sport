from rest_framework import serializers

from sport.models import Schedule


class ScheduleSerializer(serializers.Serializer):
    weekday = serializers.IntegerField()
    start = serializers.TimeField()
    end = serializers.TimeField()
    training_class = serializers.CharField(allow_null=True)


class TrainerSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    name = serializers.CharField()
    email = serializers.EmailField()


class GroupInfoSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    name = serializers.CharField()
    capacity = serializers.IntegerField()
    description = serializers.CharField()
    accredited = serializers.BooleanField()
    is_club = serializers.BooleanField()
    sport_id = serializers.IntegerField()
    sport_name = serializers.CharField()
    trainers = TrainerSerializer(many=True)

    schedule = ScheduleSerializer(many=True)
    allowed_medical_groups = serializers.ListField(child=serializers.CharField())


class ShortSportGroupSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    name = serializers.CharField()
    description = serializers.CharField()
    capacity = serializers.IntegerField()
    is_club = serializers.BooleanField()
    accredited = serializers.BooleanField()
    trainers = TrainerSerializer(many=True)
    allowed_medical_groups = serializers.ListField(child=serializers.CharField())

class DetailedSportSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    name = serializers.CharField()
    description = serializers.CharField()
    groups = ShortSportGroupSerializer(many=True)
    total_groups = serializers.IntegerField()

