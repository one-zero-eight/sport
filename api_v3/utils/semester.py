from sport.models import Semester


def get_current_semester() -> Semester:
    result = list(Semester.objects.raw("SELECT * FROM semester WHERE id = current_semester()"))
    assert len(result) == 1, "Create at least one semester for normal application work"
    return result[0]
