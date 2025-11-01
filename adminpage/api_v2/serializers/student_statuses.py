from rest_framework import serializers
from sport.models import StudentStatus

class StudentStatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = StudentStatus
        fields = ["id", "name", "description"]
