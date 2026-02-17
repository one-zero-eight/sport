from rest_framework import serializers

from api_v2.serializers.sport import NewSportSerializer
from api_v2.serializers.semester import SemesterSerializer
from sport.models import Training, Group, Trainer


class NewTrainerSerializer(serializers.ModelSerializer[Trainer]):
    id = serializers.IntegerField(source='pk')
    email = serializers.CharField(source='user.email')
    first_name = serializers.CharField(source='user.first_name')
    last_name = serializers.CharField(source='user.last_name')

    class Meta:
        model = Trainer
        fields = ('id', 'first_name', 'last_name', 'email')


class NewGroupSerializer(serializers.ModelSerializer[Group]):
    name = serializers.CharField(source='to_frontend_name')
    sport = NewSportSerializer()
    semester = SemesterSerializer()
    teachers = NewTrainerSerializer(source='trainers', many=True)
    accredited = serializers.BooleanField()

    class Meta:
        model = Group
        fields = ('id', 'name', 'capacity', 'is_club', 'sport',
                  'semester', 'teachers', 'accredited')


class TrainingInfoSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    start = serializers.DateTimeField()
    end = serializers.DateTimeField()
    group_id = serializers.IntegerField(source="group__id")
    group_name = serializers.CharField()
    sport_id = serializers.IntegerField(source="group__sport__id")
    sport_name = serializers.CharField()
    training_class_id = serializers.IntegerField(source="training_class__id")
    training_class = serializers.CharField(source="training_class__name")
    capacity = serializers.IntegerField()
    is_club = serializers.BooleanField()
    custom_name = serializers.CharField()
    load = serializers.IntegerField()

