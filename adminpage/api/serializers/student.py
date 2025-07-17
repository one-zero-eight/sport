from rest_framework import serializers
from sport.models import Student
from api.crud.crud_groups import get_trainer_groups


class StudentSerializer(serializers.Serializer):
    user_id = serializers.SerializerMethodField()
    user_statuses = serializers.SerializerMethodField()
    
    # Student-specific fields
    student_info = serializers.SerializerMethodField()
    
    # Trainer-specific fields  
    trainer_info = serializers.SerializerMethodField()

    def get_user_id(self, obj):
        """Get user ID from either Student instance or UserWrapper"""
        if hasattr(obj, 'user'):
            return str(obj.user.id)
        return None
    
    def get_user_statuses(self, obj):
        """
        Return list of all user statuses/roles
        """
        user = obj.user if hasattr(obj, 'user') else obj
        statuses = []
        
        # Check if user is superuser
        if user.is_superuser:
            statuses.append('superuser')
        
        # Check if user is staff
        if user.is_staff:
            statuses.append('staff')
        
        # Check if user has trainer profile
        if hasattr(user, 'trainer'):
            statuses.append('trainer')
        
        # Check if user has student profile
        if hasattr(user, 'student'):
            statuses.append('student')
        
        # If no specific roles, add 'user'
        if not statuses:
            statuses.append('user')
            
        return statuses
    
    def get_student_info(self, obj):
        """
        Return detailed student information if user is a student
        """
        user = obj.user if hasattr(obj, 'user') else obj
        
        if not hasattr(user, 'student'):
            return None
            
        student = user.student
        
        student_data = {
            'id': student.user.id,
            'name': student.full_name(),
            'email': student.user.email,
            'medical_group': student.medical_group.name if student.medical_group else None,
        }
        
        # Add student status if exists
        if hasattr(student, 'student_status') and student.student_status:
            student_data['student_status'] = {
                'id': student.student_status.id,
                'name': student.student_status.name,
                'description': student.student_status.description,
            }
        
        # Note: hours, debt, self_sport_hours, required_hours will be added in the view
        return student_data
    
    def get_trainer_info(self, obj):
        """
        Return detailed trainer information if user is a trainer
        """
        user = obj.user if hasattr(obj, 'user') else obj
        
        if not hasattr(user, 'trainer'):
            return None
            
        trainer = user.trainer
        
        trainer_data = {
            'id': trainer.user.id,
            'name': f"{trainer.user.first_name} {trainer.user.last_name}",
            'email': trainer.user.email,
            'groups': get_trainer_groups(trainer),
        }
        
        return trainer_data
