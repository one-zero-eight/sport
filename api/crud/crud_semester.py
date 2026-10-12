from typing import List
from sport.models import Semester


def get_ongoing_semester() -> Semester:
    """
    Retrieves current ongoing semester
    @return ongoing semester
    """
    return Semester.objects.raw('SELECT * FROM semester WHERE id = current_semester()')[0]


def get_semester_crud(current: bool, with_ft_exercises: bool) -> List[Semester]:
    if current:
        return [get_ongoing_semester()]
    elif with_ft_exercises:
        return [elem for elem in Semester.objects.filter(fitnesstestexercise__isnull=False).distinct()]
    else:
        return [elem for elem in Semester.objects.all()]
