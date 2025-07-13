from rest_framework import serializers
from sport.models import Student


class StudentSerializer(serializers.ModelSerializer[Student]):
    id = serializers.CharField(source='user.id')
    name = serializers.CharField(source='full_name')
    email = serializers.EmailField(source='user.email')
    medical_group = serializers.CharField(source='medical_group.name')
    
    # Fields for student sport hours
    hours_not_self = serializers.FloatField(read_only=True)
    hours_self_not_debt = serializers.FloatField(read_only=True)
    hours_self_debt = serializers.FloatField(read_only=True)
    hours_total = serializers.FloatField(read_only=True)
    hours_required = serializers.IntegerField(read_only=True)
    debt = serializers.IntegerField(read_only=True)

    class Meta:
        model = Student
        fields = ('id', 'name', 'email', 'medical_group', 'hours_not_self', 
                 'hours_self_not_debt', 'hours_self_debt', 'hours_total', 
                 'hours_required', 'debt')
