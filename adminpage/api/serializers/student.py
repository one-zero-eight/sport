from rest_framework import serializers
from sport.models import Student


class StudentSerializer(serializers.ModelSerializer[Student]):
    id = serializers.CharField(source='user.id')
    name = serializers.CharField(source='full_name')
    email = serializers.EmailField(source='user.email')
    medical_group = serializers.CharField(source='medical_group.name')
    
    # Fields for student sport hours
    hours = serializers.FloatField(read_only=True)
    debt = serializers.IntegerField(read_only=True)
    self_sport_hours = serializers.FloatField(read_only=True)
    required_hours = serializers.FloatField(read_only=True)  # Required hours threshold for current semester

    class Meta:
        model = Student
        fields = ('id', 'name', 'email', 'medical_group', 'hours', 'debt', 'self_sport_hours', 'required_hours')
