from typing import List, Dict

from django.db import transaction, connection

from api.crud import dictfetchall
from sport.models import Student, Enroll, Group


@transaction.atomic
def enroll_student(group: Group, student: Student):
    """
    Enrolls given student in a group
    """

    Enroll.objects.create(student=student, group=group)


def unenroll_student(group: Group, student: Student) -> int:
    """
    Unenroll given student from a group
    """
    removed_count, _ = Enroll.objects.filter(
        student=student,
        group=group,
    ).delete()
    return removed_count


def get_primary_groups(semester_id: int) -> Dict[int, int]:
    if semester_id is None or not isinstance(semester_id, int):
        raise ValueError("semester_id must be int")
    with connection.cursor() as cursor:
        cursor.execute(
            'select * from get_primary_groups_in_semester(%s);',
            [semester_id],
        )
        primary_groups_list = dictfetchall(cursor)
    result = {}
    for row in primary_groups_list:
        result.update({
            row['student_id']: row['group_id'],
        })
    return result
