from rest_framework import serializers

from sport.models import Schedule


class ScheduleSerializer(serializers.Serializer):
    weekday = serializers.IntegerField()
    weekday_name = serializers.CharField()
    start_time = serializers.CharField()
    end_time = serializers.CharField()
    training_class = serializers.CharField(allow_null=True)
    training_ids = serializers.ListField(child=serializers.IntegerField(), allow_empty=True)



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


class TrainingParticipantSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    name = serializers.CharField()
    email = serializers.EmailField()
    medical_group = serializers.CharField()
    hours = serializers.FloatField()
    attended = serializers.BooleanField()


class TrainingParticipantsInfoSerializer(serializers.Serializer):
    total_checked_in = serializers.IntegerField()
    students = TrainingParticipantSerializer(many=True)


class ClubTrainingSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    start = serializers.DateTimeField()
    end = serializers.DateTimeField()
    training_class = serializers.CharField(allow_null=True)
    group_accredited = serializers.BooleanField()
    can_grade = serializers.BooleanField()
    can_check_in = serializers.BooleanField()
    checked_in = serializers.BooleanField()
    participants = TrainingParticipantsInfoSerializer()
    capacity = serializers.IntegerField()
    available_spots = serializers.IntegerField()


class DetailedGroupSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    name = serializers.CharField()
    description = serializers.CharField()
    capacity = serializers.IntegerField()
    current_enrollment = serializers.IntegerField()
    is_club = serializers.BooleanField()
    accredited = serializers.BooleanField()
    trainings = ClubTrainingSerializer(many=True)
    trainers = TrainerSerializer(many=True)
    allowed_medical_groups = serializers.ListField(child=serializers.CharField())


class DetailedSportSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    name = serializers.CharField()
    description = serializers.CharField()
    groups = DetailedGroupSerializer(many=True)
    total_groups = serializers.IntegerField()


class SportsWithGroupsSerializer(serializers.Serializer):
    sports = DetailedSportSerializer(many=True)
