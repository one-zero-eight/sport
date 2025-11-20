from rest_framework import serializers

from sport.models import MedicalGroup


class MedicalGroupSerializer(serializers.ModelSerializer[MedicalGroup]):
    class Meta:
        model = MedicalGroup
        fields = "__all__"
