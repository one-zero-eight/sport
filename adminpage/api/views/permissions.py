from rest_framework.permissions import BasePermission

class IsAuthenticatedStudent(BasePermission):
    def has_permission(self, request, view):
        return hasattr(request, 'current_student')
