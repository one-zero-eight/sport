from rest_framework import serializers
from sport.models import Student


class StudentSerializer(serializers.ModelSerializer[Student]):
    id = serializers.CharField(source='user.id')
    name = serializers.CharField(source='full_name')
    email = serializers.EmailField(source='user.email')
    medical_group = serializers.CharField(source='medical_group.name')
    user_status = serializers.SerializerMethodField()
    
    # Fields for student sport hours
    hours = serializers.FloatField(read_only=True)
    debt = serializers.IntegerField(read_only=True)
    self_sport_hours = serializers.FloatField(read_only=True)
    required_hours = serializers.FloatField(read_only=True)  # Required hours threshold for current semester

    class Meta:
        model = Student
        fields = ('id', 'name', 'email', 'medical_group', 'user_status', 'hours', 'debt', 'self_sport_hours', 'required_hours')
    
    def get_user_status(self, obj):
        """
        Determine user status based on user properties and related models
        """
        user = obj.user
        
        # Check if user is superuser
        if user.is_superuser:
            return 'superuser'
        
        # Check if user is staff
        if user.is_staff:
            return 'staff'
        
        # Check if user has trainer profile
        if hasattr(user, 'trainer'):
            return 'trainer'
        
        # Check if user has student profile
        if hasattr(user, 'student'):
            return 'student'
        
        # Default fallback
        return 'user'
