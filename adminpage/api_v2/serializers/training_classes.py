from rest_framework import serializers
from sport.models import TrainingClass


class TrainingClassesSerializer(serializers.ModelSerializer[TrainingClass]):
    class Meta:
        model = TrainingClass
        fields = ('id', 'name')

