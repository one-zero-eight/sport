from rest_framework import serializers
from sport.models import TrainingClass


class TrainingClassSerializer(serializers.ModelSerializer[TrainingClass]):
    class Meta:
        model = TrainingClass
        fields = ('id', 'name')
