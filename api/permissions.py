from rest_framework import permissions
from rest_framework.permissions import IsAdminUser

from accounts.models import User


def is_student(user: User) -> bool:
    return user.student_or_none and user.student_or_none.student_status.name == 'Normal'


def is_trainer(user: User) -> bool:
    return user.trainer_or_none is not None


class IsStudent(permissions.BasePermission):
    def has_permission(self, request, view):
        if is_student(request.user):
            return True
        return False


class SportSelected(IsStudent):
    def has_permission(self, request, view):
        return super().has_permission(request, view) and request.user.student.sport


class IsTrainer(permissions.BasePermission):
    def has_permission(self, request, view):
        return is_trainer(request.user)


class IsStaff(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.is_staff


class IsSuperUser(IsAdminUser):
    def has_permission(self, request, view):
        return request.user.is_superuser
