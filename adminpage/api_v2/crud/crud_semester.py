from typing import List
from sport.models import Semester


def get_semesters_crud() -> List[Semester]:
    return [elem for elem in Semester.objects.all()]


def get_semester_by_id_crud(semester_id: int) -> List[Semester]:
    """
    Retrieves a semester by its ID.
    @param semester_id: integer ID of the semester
    @return Semester object if found, otherwise None
    """
    return Semester.objects.get(id=semester_id)

def get_current_semester_crud() -> Semester:
    """
    Retrieves current ongoing semester
    @return ongoing semester
    """
    return Semester.objects.raw('SELECT * FROM semester WHERE id = current_semester()')[0]