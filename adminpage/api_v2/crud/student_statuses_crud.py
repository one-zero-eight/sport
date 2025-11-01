from sport.models import StudentStatus
from typing import List

def get_student_statuses_crud() -> List[StudentStatus]:
    """Return all available student statuses"""
    return list(StudentStatus.objects.all())
