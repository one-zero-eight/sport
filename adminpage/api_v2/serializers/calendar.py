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
