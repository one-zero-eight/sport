from rest_framework import permissions
from rest_framework.permissions import IsAdminUser

from accounts.models import User


def is_student(user: User) -> bool:
    if not user.is_authenticated:
        return False
    student = user.student_or_none
    return student is not None and student.student_status.name == "Normal"


def is_trainer(user: User) -> bool:
    if not user.is_authenticated:
        return False
    return user.trainer_or_none is not None


class IsStudent(permissions.BasePermission):
    def has_permission(self, request, view):
        return bool(is_student(request.user))


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
