from django.db.models import Q
from sport.models import Group, Student


def education_level_q_for_group(student: Student) -> Q:
    """Same rule as api.crud.crud_groups.get_sports (student branch)."""
    return Q(allowed_education_level__in=[-1, 2 if student.is_college else 1])


def education_level_q_for_training_group(student: Student) -> Q:
    """Same rule as api.crud.crud_training.get_trainings_for_student."""
    return Q(group__allowed_education_level__in=[-1, 2 if student.is_college else 1])


def student_can_view_group(student: Student, group: Group) -> bool:
    """Parity with get_sports(student) filters for a single group."""
    if student.medical_group_id is None:
        return False
    if not group.allowed_medical_groups.filter(pk=student.medical_group_id).exists():
        return False
    if group.allowed_education_level not in (-1, 2 if student.is_college else 1):
        return False
    return True
