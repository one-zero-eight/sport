from rest_framework import serializers
from sport.models import TrainingClass


class TrainingClassesSerializer(serializers.ModelSerializer[TrainingClass]):
    class Meta:
        model = TrainingClass
        fields = ('id', 'name')


# class TrainingCheckInRequest(serializers.Serializer):
#     check_in = serializers.BooleanField(
#         help_text="True — check in; False — cancel check-in",
#         required=True
#     )