import csv
import datetime
import io
import math

from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import connection
from django.db.models import F, Q, IntegerField, OuterRef
from django.db.models.expressions import ExpressionWrapper, Subquery
from django.db.models.functions import Coalesce
from django.utils import timezone
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import Response
from pydantic import BaseModel
from starlette import status

from api_v3.dependencies import VerifiedDep
from api_v3.utils.search import search_students
from api_v3.utils.semester import get_current_semester
from api_v3.permissions import is_trainer_of_group, is_admin
from sport.models import Training, Group, Student, Attendance, Debt


def _dictfetchall(cursor) -> list[dict]:
    columns = [col[0] for col in cursor.description]
    return [dict(zip(columns, row)) for row in cursor.fetchall()]


class SumSubquery(Subquery):
    output_field = None

    def __init__(self, queryset, sum_by, output_field=IntegerField(), **extra):
        super().__init__(queryset, output_field, **extra)
        self.output_field = output_field
        self.template = "(SELECT sum({}) FROM (%(subquery)s) _sum)".format(sum_by)


def _get_students_grades(training_id: int) -> list[dict]:
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT
                u.id AS student_id,
                u.first_name,
                u.last_name,
                u.email,
                COALESCE(a.hours, 0) AS hours,
                m.id AS med_group_id,
                m.name AS med_group_name,
                m.description AS med_group_description
            FROM auth_user u
            JOIN student s ON s.user_id = u.id
            LEFT JOIN medical_group m ON m.id = s.medical_group_id
            LEFT JOIN attendance a
                ON a.student_id = u.id AND a.training_id = %(training_id)s
            WHERE u.id IN (
                SELECT student_id FROM attendance WHERE training_id = %(training_id)s
                UNION
                SELECT student_id FROM sport_trainingcheckin WHERE training_id = %(training_id)s
            )
            """,
            {"training_id": training_id},
        )
        rows = _dictfetchall(cursor)
    for row in rows:
        row["id"] = row["student_id"]
        row["full_name"] = f"{row['first_name']} {row['last_name']}".strip()
        if row.get("med_group_id") is not None:
            row["medical_group"] = {
                "id": row.pop("med_group_id"),
                "name": row.pop("med_group_name"),
                "description": row.pop("med_group_description"),
            }
            row["med_group"] = row["medical_group"]["name"]
        else:
            row["medical_group"] = None
            row["med_group"] = None
    return rows


router = APIRouter(
    tags=["Trainings attendance"],
    responses={
        401: {"description": "Invalid token"},
        403: {"description": "Unauthorized"},
    },
)

User = get_user_model()


class AttendanceSuggestionSchema(BaseModel):
    id: int
    first_name: str
    last_name: str
    email: str
    medical_group: str | None = None


class AttendanceStudentGradeSchema(BaseModel):
    id: int
    first_name: str
    last_name: str
    email: str
    medical_group: str | None = None
    hours: float


class TrainingGradesSchema(BaseModel):
    group_name: str
    start: datetime.datetime
    academic_duration: int
    grades: list[AttendanceStudentGradeSchema]


class GradeSetSchema(BaseModel):
    student_id: int
    hours: float


class AttendanceMarkSchema(BaseModel):
    training_id: int
    students_hours: list[GradeSetSchema]


class BadGradeReportGradeSchema(BaseModel):
    email: str
    hours: float


class BadGradeReportSchema(BaseModel):
    code: int
    description: str
    negative_marks: list[BadGradeReportGradeSchema] | None = None
    overflow_marks: list[BadGradeReportGradeSchema] | None = None


class StudentHoursSummarySchema(BaseModel):
    semester_id: float
    debt: float
    self_sport_hours: float
    hours_from_groups: float
    required_hours: float


class AttendanceErrors:
    TRAINING_NOT_EDITABLE = (
        2,
        f"Training not editable before it or after "
        f"{settings.TRAINING_EDITABLE_INTERVAL.days} days",
    )
    OUTBOUND_GRADES = (
        3,
        "Some students received negative marks or more than maximum",
    )


@router.get(
    "/trainings/{training_id}/suggest-student",
    responses={
        200: {"description": "Suggest students for attendance"},
        404: {"description": "Group not found"},
    },
)
def suggest_student(
    user: VerifiedDep,
    training_id: int,
    term: str = Query(..., description="Search term"),
    group_id: int = Query(..., description="Group id of the training"),
) -> list[AttendanceSuggestionSchema]:
    """
    Suggest students based on search term for attendance marking.
    """
    try:
        group = Group.objects.get(pk=group_id)
    except Group.DoesNotExist:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Group not found",
        )

    if not (is_trainer_of_group(user, group) or is_admin(user)):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not allowed to get student suggestions for this training",
        )

    not_banned = ~Q(user_id__in=group.banned_students.values_list("user_id", flat=True))
    allowed = (
        Q(user_id__in=group.allowed_students.values_list("user_id", flat=True))
        | Q(medical_group__in=group.allowed_medical_groups.all())
    )
    suggested_students = search_students(
        term, requirement=not_banned & allowed
    )
    return [
        AttendanceSuggestionSchema(
            id=s["id"],
            first_name=s["first_name"],
            last_name=s["last_name"],
            email=s["email"],
            medical_group=s.get("medical_group"),
        )
        for s in suggested_students
    ]


@router.get(
    "/trainings/{training_id}/attendance.csv",
    responses={
        200: {"description": "Get training grades in CSV"},
        404: {"description": "Training not found"},
    },
)
def get_training_attendance_csv(
    user: VerifiedDep,
    training_id: int,
) -> Response:
    """
    Get training grades as CSV.
    """
    try:
        training = Training.objects.get(pk=training_id)
    except Training.DoesNotExist:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Training not found",
        )

    group: Group = training.group
    if not (is_trainer_of_group(user, group) or is_admin(user)):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not allowed to view training attendance",
        )

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Student ID", "Full Name", "Email", "Medical Group", "Hours"])
    for student in _get_students_grades(training_id):
        writer.writerow(
            [
                student["student_id"],
                student["full_name"],
                student["email"],
                student["med_group"],
                student["hours"],
            ]
        )

    csv_content = output.getvalue()
    return Response(
        content=csv_content,
        media_type="text/csv",
        headers={
            "Content-Disposition": f'attachment; filename="training-{training_id}.csv"'
        },
    )


@router.get(
    "/trainings/{training_id}/attendance",
    responses={
        200: {"description": "Get training grades"},
        404: {"description": "Training not found"},
    },
)
def get_training_attendance(
    user: VerifiedDep,
    training_id: int,
) -> TrainingGradesSchema:
    """
    Get student grades for a specific training session.
    """
    try:
        training = Training.objects.get(pk=training_id)
    except Training.DoesNotExist:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Training not found",
        )

    group: Group = training.group
    if not (is_trainer_of_group(user, group) or is_admin(user)):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not allowed to view training attendance",
        )

    grades = _get_students_grades(training_id)

    grade_items: list[AttendanceStudentGradeSchema] = []
    for g in grades:
        grade_items.append(
            AttendanceStudentGradeSchema(
                id=g["id"],
                first_name=g["first_name"],
                last_name=g["last_name"],
                email=g["email"],
                medical_group=g.get("med_group"),
                hours=g["hours"],
            )
        )

    payload = TrainingGradesSchema(
        group_name=group.to_frontend_name(),
        start=training.start,
        grades=grade_items,
        academic_duration=training.academic_duration,
    )
    return payload


@router.post(
    "/trainings/{training_id}/attendance",
    responses={
        200: {"description": "Mark student attendance"},
        400: {"description": "Invalid grades"},
        404: {"description": "Training not found"},
    },
)
def mark_training_attendance(
    user: VerifiedDep,
    training_id: int,
    body: AttendanceMarkSchema,
) -> list[BadGradeReportGradeSchema] | BadGradeReportSchema:
    """
    Mark attendance and assign hours for students in a training session.
    """
    try:
        training = (
            Training.objects.select_related("group")
            .only("group__trainers__user", "start", "end")
            .get(pk=training_id)
        )
    except Training.DoesNotExist:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Training not found",
        )

    if not (is_trainer_of_group(user, training.group) or is_admin(user)):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not allowed to mark attendance",
        )

    now = timezone.now()
    if not (
        training.start
        <= now
        <= training.start + settings.TRAINING_EDITABLE_INTERVAL
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=BadGradeReportSchema(
                code=AttendanceErrors.TRAINING_NOT_EDITABLE[0],
                description=AttendanceErrors.TRAINING_NOT_EDITABLE[1],
                negative_marks=[],
                overflow_marks=[],
            ).model_dump(),
        )

    id_to_hours = {
        item.student_id: item.hours for item in body.students_hours
    }

    max_hours = training.academic_duration
    students = User.objects.filter(pk__in=id_to_hours.keys()).only("email")

    hours_to_mark: list[tuple[User, float]] = []
    negative_mark: list[BadGradeReportGradeSchema] = []
    overflow_mark: list[BadGradeReportGradeSchema] = []

    for student in students:
        hours_put = id_to_hours[student.pk]
        if hours_put < 0:
            negative_mark.append(BadGradeReportGradeSchema(email=student.email, hours=hours_put))
        elif hours_put > max_hours:
            overflow_mark.append(BadGradeReportGradeSchema(email=student.email, hours=hours_put))
        elif (
            str(
                Student.objects.filter(
                    user=get_user_model().objects.filter(email=student.email)[0]
                )[0].student_status
            )
            != "Normal"
        ):
            continue
        else:
            hours_to_mark.append((student, hours_put))

    if negative_mark or overflow_mark:
        code, description = AttendanceErrors.OUTBOUND_GRADES
        bad_payload = BadGradeReportSchema(
            code=code,
            description=description,
            negative_marks=negative_mark,
            overflow_marks=overflow_mark,
        )
        return bad_payload

    mark_data = [(x[0].pk, x[1]) for x in hours_to_mark]
    for student_id, student_mark in mark_data:
        if student_id <= 0 or student_mark < 0.0:
            raise ValueError(
                f"All students id and marks must be non-negative, got {(student_id, student_mark)}"
            )
        if math.floor(student_mark) >= 1000:
            raise ValueError(
                f"All students marks must floor to less than 1000, got {student_mark}"
            )

    with connection.cursor() as cursor:
        args_add = [
            (student_id, training.pk, student_mark)
            for student_id, student_mark in mark_data
            if student_mark > 0
        ]
        args_del = [
            (student_id, training.pk)
            for student_id, student_mark in mark_data
            if student_mark == 0
        ]
        if args_add:
            args_add_str = b",".join(cursor.mogrify("(%s, %s, %s)", x) for x in args_add)
            cursor.execute(
                f"INSERT INTO attendance (student_id, training_id, hours) VALUES {args_add_str.decode()} "
                "ON CONFLICT ON CONSTRAINT unique_attendance DO UPDATE SET hours=excluded.hours"
            )
        if args_del:
            args_del_str = b",".join(cursor.mogrify("(%s, %s)", x) for x in args_del)
            cursor.execute(
                f"DELETE FROM attendance WHERE (student_id, training_id) IN ({args_del_str.decode()})"
            )

    ok_payload = [
        BadGradeReportGradeSchema(
            email=x[0].email,
            hours=x[1],
        )
        for x in hours_to_mark
    ]
    return ok_payload


@router.get(
    "/students/{student_id}/hours-summary",
    responses={
        200: {"description": "Get student hours summary"},
        404: {"description": "Student not found"},
    },
)
def get_student_hours_summary(
    user: VerifiedDep,
    student_id: int,
) -> StudentHoursSummarySchema:
    """
    Get comprehensive student hours summary.
    """
    if not (user.id == student_id or is_admin(user)):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to view this student's hours summary",
        )

    try:
        Student.objects.get(user_id=student_id)
    except Student.DoesNotExist:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student not found",
        )

    current_semester = get_current_semester()
    current_attendance = Attendance.objects.filter(
        student_id=student_id,
        training__group__semester=current_semester,
    )

    hours_from_groups = 0.0
    self_sport_hours = 0.0
    for attendance in current_attendance:
        if attendance.cause_report is None:
            hours_from_groups += float(attendance.hours)
        elif attendance.cause_report.debt is False:
            self_sport_hours += float(attendance.hours)

    try:
        debt = Debt.objects.get(
            semester_id=current_semester.id, student_id=student_id
        ).debt
    except Debt.DoesNotExist:
        debt = 0.0

    return StudentHoursSummarySchema(
        semester_id=current_semester.id,
        debt=float(debt),
        self_sport_hours=float(self_sport_hours),
        hours_from_groups=float(hours_from_groups),
        required_hours=float(current_semester.hours),
    )


class BetterThanInfoSchema(BaseModel):
    better_than: float


@router.get(
    "/students/{student_id}/better-than",
    responses={
        200: {"description": "Get student performance ranking"},
    },
)
def get_better_than_info(
    user: VerifiedDep,
    student_id: int,
) -> BetterThanInfoSchema:
    """
    Get student's performance ranking compared to other students.
    """
    if not (user.id == student_id or is_admin(user)):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to view this student's hours summary",
        )

    try:
        Student.objects.get(user_id=student_id)
    except Student.DoesNotExist:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student not found",
        )

    current_semester = get_current_semester()
    qs = Student.objects.all().annotate(
        _debt=Coalesce(
            SumSubquery(
                Debt.objects.filter(
                    semester_id=current_semester.pk, student_id=OuterRef("pk")
                ),
                "debt",
            ),
            0,
        )
    )
    qs = qs.annotate(
        _ongoing_semester_hours=Coalesce(
            SumSubquery(
                Attendance.objects.filter(
                    training__group__semester_id=current_semester.pk,
                    student_id=OuterRef("pk"),
                ),
                "hours",
            ),
            0,
        )
    )
    qs = qs.annotate(
        complex_hours=ExpressionWrapper(
            F("_ongoing_semester_hours") - F("_debt"),
            output_field=IntegerField(),
        )
    )
    student_hours = qs.get(pk=student_id).complex_hours
    if student_hours <= 0:
        return BetterThanInfoSchema(better_than=0)

    all_count = qs.filter(complex_hours__gt=0).count()
    if all_count == 1:
        return BetterThanInfoSchema(better_than=100)

    worse = qs.filter(complex_hours__gt=0, complex_hours__lt=student_hours).count()
    return BetterThanInfoSchema(better_than=round(worse / (all_count - 1) * 100, 1))

