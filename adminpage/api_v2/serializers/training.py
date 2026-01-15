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


class TrainingInfoSerializer(serializers.ModelSerializer[Training]):
    group = NewGroupSerializer()
    load = serializers.SerializerMethodField()
    place = serializers.CharField(source='training_class')

    def get_load(self, obj: Training) -> int:
        return obj.checkins.count()

    class Meta:
        model = Training
        fields = ('id', 'custom_name', 'group',
                  'start', 'end', 'load', 'place')


