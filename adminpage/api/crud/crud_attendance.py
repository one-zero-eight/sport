from math import floor
from typing import Iterable, Tuple, List

from django.db.models import F, Value, BooleanField, Case, When, CharField, Sum, IntegerField, OuterRef
from django.db.models.functions import Concat, Coalesce
from django.db.models.expressions import Value, Case, When, Subquery, OuterRef, ExpressionWrapper
from typing import TypedDict

from django.db import connection

from api.crud.utils import dictfetchall
from sport.models import Student, Semester, Training, SelfSportReport, Reference, Debt

from api.crud.crud_semester import get_ongoing_semester
from sport.models import Attendance
from .utils import SumSubquery


VTrue = Value(True, output_field=BooleanField())
VFalse = Value(False, output_field=BooleanField())


class BriefHours(TypedDict):
    semester_id: int
    semester_name: str
    semester_start: str
    semester_end: str
    hours: int


def get_brief_hours(student: Student) -> List[BriefHours]:
    """
    Retrieves statistics of hours per different semesters
    """
    hours = get_student_hours(student)
    hours = [hours['ongoing_semester']] + hours['last_semesters_hours']

    brief_hours: List[BriefHours] = []
    for sem in hours:
        semester = Semester.objects.get(id=sem['id_sem'])
        # skip semester if it matches the enrollment_year but Spring
        if student.enrollment_year >= semester.start.year and \
                (student.enrollment_year != semester.start.year or semester.start.month <= 7):  # semester before august
            continue
        element: BriefHours = {
            'semester_id': semester.id,
            'semester_name': semester.name,
            'semester_start': semester.start.strftime("%b. %d, %Y"),
            'semester_end': semester.end.strftime("%b. %d, %Y"),
            'hours': int(sem['hours_not_self'] + sem['hours_self_not_debt'] + sem['hours_self_debt'])
        }
        brief_hours.append(element)

    return brief_hours


def get_detailed_hours(student: Student, semester: Semester):
    """
    Retrieves statistics of hours in one semester
    """
    with connection.cursor() as cursor:
        cursor.execute(
            'SELECT g.name AS "group", t.custom_name AS custom_name, t.start AS "timestamp", a.hours AS hours '
            'FROM training t, "group" g, attendance a '
            'WHERE a.student_id = %s '
            'AND a.training_id = t.id '
            'AND t.group_id = g.id '
            'AND g.semester_id = %s '
            'ORDER BY t.start', (student.pk, semester.pk))
        return dictfetchall(cursor)


def get_detailed_hours_and_self(student, semester: Semester):
    """
    Retrieves statistics of hours in one semester
    """
    att = (Attendance.objects
           .filter(training__group__semester=semester, student=student.student)
           .annotate(
               group=F("training__group__name"),
               group_id=F("training__group_id"),
               custom_name=F("training__custom_name"),
               timestamp=Case(When(cause_report__isnull=False, then=F('cause_report__uploaded')),
                              When(cause_reference__isnull=False,
                                   then=F('cause_reference__uploaded')),
                              default=F('training__start')),
               approved=Case(When(hours__gt=0, then=VTrue), default=VFalse)
           )
           .values('group_id', 'group', 'custom_name', 'timestamp', 'hours', 'approved'))


    self = (SelfSportReport.objects
            .filter(semester=semester, student=student.student, attendance=None)
            .annotate(
                group=Value('Self training', output_field=CharField()),
                group_id=Value(-1, output_field=IntegerField()),
                custom_name=Concat(
                    Value('[Self] ', output_field=CharField()), F('training_type__name')),
                timestamp=F("uploaded"),
                approved=F('approval')
            )
            .values('group_id', 'group', 'custom_name', 'timestamp', 'hours', 'approved'))

    ref = (Reference.objects
           .filter(semester=semester, student=student.student, attendance=None)
           .annotate(
               group=Value('Medical leave', output_field=CharField()),
               group_id=Value(-1, output_field=IntegerField()),
               custom_name=Value(None, output_field=CharField()),
               timestamp=F("uploaded"),
               approved=F('approval')
           )
           .values('group_id', 'group', 'custom_name', 'timestamp', 'hours', 'approved'))

    return att.union(self).union(ref).order_by('timestamp')


def mark_hours(training: Training, student_hours: Iterable[Tuple[int, float]]):
    """
    Puts hours for one training session to one student. If hours for session were already put, updates it
    @param training: given training
    @param student_hours: iterable with items (<student_id:int>, <student_hours:float>)
    """
    for student_id, student_mark in student_hours:
        if student_id <= 0 or student_mark < 0.0:
            raise ValueError(
                f"All students id and marks must be non-negative, got {(student_id, student_mark)}")
        # Currently hours field is numeric(5,2), so
        # A field with precision 5, scale 2 must round to an absolute value less than 10^3.
        floor_max = 1000  # TODO: hardcoded limit
        if floor(student_mark) >= floor_max:
            raise ValueError(f"All students marks must floor to less than {floor_max}, "
                             f"got {student_mark} -> {floor(student_mark)} >= {floor_max}")
    with connection.cursor() as cursor:
        args_add_str = b",".join(
            cursor.mogrify("(%s, %s, %s)", (student_id,
                           training.pk, student_mark))
            for student_id, student_mark in student_hours if student_mark > 0
        )
        args_del_str = b",".join(
            cursor.mogrify("(%s, %s)", (student_id, training.pk))
            for student_id, student_mark in student_hours if student_mark == 0
        )
        if len(args_add_str) > 0:
            cursor.execute(f'INSERT INTO attendance (student_id, training_id, hours) VALUES {args_add_str.decode()} '
                           f'ON CONFLICT ON CONSTRAINT unique_attendance '
                           f'DO UPDATE set hours=excluded.hours')
        if len(args_del_str) > 0:
            cursor.execute(f'DELETE FROM attendance '
                           f'WHERE  (student_id, training_id) IN ({args_del_str.decode()})')


def toggle_has_QR(student: Student):
    """
    Toggles student's QR presence
    """
    student.has_QR = not student.has_QR
    student.save()


class SemesterHours(TypedDict):
    id_sem: int
    hours_not_self: float
    hours_self_not_debt: float
    hours_self_debt: float
    hours_sem_max: int


def get_student_hours(student_id, **kwargs) -> TypedDict('StudentHours',
                                                         {'last_semesters_hours': List[SemesterHours],
                                                          'ongoing_semester': SemesterHours}):
    student = Student.objects.get(user_id=student_id)
    sem_info_cur = {"id_sem": 0, "hours_not_self": 0.0, "hours_self_not_debt": 0.0,
                    "hours_self_debt": 0.0, "hours_sem_max": 0.0, "debt": 0.0}

    query_attend_current_semester = Attendance.objects.filter(student_id=student_id,
                                                              training__group__semester=get_ongoing_semester())
    sem_info_cur['id_sem'] = get_ongoing_semester().id
    sem_info_cur['hours_sem_max'] = get_ongoing_semester().hours

    try:
        sem_info_cur['debt'] = Debt.objects.get(
            semester_id=get_ongoing_semester().id, student_id=student_id).debt
    except Debt.DoesNotExist:
        sem_info_cur['debt'] = 0

    for sem in query_attend_current_semester:
        if sem.cause_report is None:
            sem_info_cur['hours_not_self'] += float(sem.hours)
        elif sem.cause_report.debt is True:
            sem_info_cur['hours_self_debt'] += float(sem.hours)
        else:
            sem_info_cur['hours_self_not_debt'] += float(sem.hours)

    sem_info = {"id_sem": 0, "hours_not_self": 0.0, "hours_self_not_debt": 0.0,
                "hours_self_debt": 0.0, "hours_sem_max": 0.0, "debt": 0.0}
    last_sem_info_arr = []

    last_semesters = Semester.objects.filter(
        end__lt=get_ongoing_semester().start).order_by('-end')

    for sem in last_semesters:
        if student in sem.academic_leave_students.all():
            pass
        elif sem.end.year >= student.enrollment_year:
            sem_info["id_sem"] = sem.id
            sem_info["hours_sem_max"] = sem.hours
            try:
                sem_info['debt'] = Debt.objects.get(semester_id=get_ongoing_semester().id,
                                                    student_id=student_id).debt
            except Debt.DoesNotExist:
                sem_info['debt'] = 0
            query_attend_last_semester = Attendance.objects.filter(student_id=student_id,
                                                                   training__group__semester=sem)
            for att in query_attend_last_semester:
                if att.cause_report is None:
                    sem_info['hours_not_self'] += float(att.hours)
                elif att.cause_report.debt is True:
                    sem_info['hours_self_debt'] += float(att.hours)
                else:
                    sem_info['hours_self_not_debt'] += float(att.hours)
            last_sem_info_arr.append(sem_info)
            sem_info = {"id_sem": 0, "hours_not_self": 0.0, "hours_self_not_debt": 0.0,
                        "hours_self_debt": 0.0, "hours_sem_max": 0.0, "debt": 0.0}
    return {
        "last_semesters_hours": last_sem_info_arr,
        "ongoing_semester": sem_info_cur
    }


def get_negative_hours(student_id, hours_info=None, **kwargs):
    student_hours = get_student_hours(
        student_id) if hours_info is None else hours_info
    sem_now = student_hours['ongoing_semester']
    try:
        debt = Debt.objects.get(
            student=student_id, semester=get_ongoing_semester()).debt
    except:
        debt = 0
    res = sem_now['hours_self_debt'] + sem_now['hours_not_self'] + \
        sem_now['hours_self_not_debt'] - debt

    return res


def create_debt(last_semester, **kwargs):
    # TODO: add debt when new semester starts
    pass


def better_than(student_id):
    qs = Student.objects.all().annotate(_debt=Coalesce(
        SumSubquery(Debt.objects.filter(semester_id=get_ongoing_semester().pk,
                                        student_id=OuterRef("pk")), 'debt'),
        0
    ))

    qs = qs.annotate(_ongoing_semester_hours=Coalesce(
        SumSubquery(Attendance.objects.filter(
            training__group__semester_id=get_ongoing_semester().pk, student_id=OuterRef("pk")), 'hours'),
        0
    ))

    qs = qs.annotate(complex_hours=ExpressionWrapper(
        F('_ongoing_semester_hours') - F('_debt'), output_field=IntegerField()
    ))

    student_hours = qs.get(pk=student_id).complex_hours
    if student_hours <= 0:
        return 0

    all = qs.filter(complex_hours__gt=0, ).count()
    if all == 1:
        return 100

    worse = qs.filter(complex_hours__gt=0,
                      complex_hours__lt=student_hours).count()

    return round(worse / (all - 1) * 100, 1)
