from collections import defaultdict
from datetime import date, datetime

from django.db.models import F, Q
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from starlette import status

from api_v3.utils.semester import get_current_semester
from api_v3.dependencies import VerifiedDep
from api_v3.permissions import is_student
from api_v3.routers.fitness_test import FitnessTestSessionSchema
from sport.models import Semester, Group, FitnessTestResult, FitnessTestSession, Student, FitnessTestGrading

router = APIRouter(
    tags=["Students"],
    responses={
        401: {"description": "Invalid token"},
        403: {"description": "Unauthorized"},
    },
)


class TrainingHistorySchema(BaseModel):
    training_id: int
    date: str
    time: str
    hours: int
    group_name: str | None = None
    sport_name: str | None = None
    training_class: str | None = None
    custom_name: str | None = None


class TrainingHistoryRowSchema(BaseModel):
    group_id: int
    group: str
    custom_name: str | None
    timestamp: datetime
    hours: int
    approved: bool


class FitnessTestExerciseResultSchema(BaseModel):
    exercise_id: int
    exercise_name: str
    unit: str | None
    value: int
    display_value: str
    score: int
    max_score: int


class FitnessTestStudentSessionResultSchema(BaseModel):
    session: FitnessTestSessionSchema
    exercise_results: list[FitnessTestExerciseResultSchema]
    total_score: int
    max_score: int
    passed: bool


def build_fitness_test_session_result(
    session: FitnessTestSession,
    results: list[FitnessTestResult],
    student: Student,
    ongoing_semester_id: int | None,
) -> FitnessTestStudentSessionResultSchema:
    exercise_results = [
        FitnessTestExerciseResultSchema(
            exercise_id=result.exercise_id,
            exercise_name=result.exercise.exercise_name,
            unit=result.exercise.value_unit,
            value=result.value,
            display_value=(
                f"{result.value} {result.exercise.value_unit}".strip()
                if result.exercise.select is None
                else result.exercise.select.split(",")[result.value]
            ),
            score=get_score(student, result),
            max_score=get_max_score(student, result),
        )
        for result in results
    ]
    total_score = sum(result.score for result in exercise_results)
    max_score = sum(result.max_score for result in exercise_results)
    grade = all(
        exercise.score >= result.exercise.threshold
        for exercise, result in zip(exercise_results, results)
    )
    if (
        session.semester_id == ongoing_semester_id
        and student.medical_group_id == 0
        and results
    ):
        grade = True
    else:
        grade = grade and total_score >= session.semester.points_fitness_test

    return FitnessTestStudentSessionResultSchema(
        session=FitnessTestSessionSchema.model_validate(session, from_attributes=True),
        exercise_results=exercise_results,
        total_score=total_score,
        max_score=max_score,
        passed=grade,
    )


class SemesterHistorySchema(BaseModel):
    semester_id: int
    semester_name: str
    semester_start: date
    semester_end: date
    required_hours: int
    total_hours: int
    trainings: list[TrainingHistorySchema]
    fitness_tests: list[FitnessTestStudentSessionResultSchema]


@router.get(
    "/students/{student_id}/semester-history/{semester_id}",
    responses={
        200: {"description": "Get student training history for specific semester"},
        404: {"description": "Semester not found"},
    },
)
def get_student_specific_semester_history(
    user: VerifiedDep,
    student_id: int,
    semester_id: int,
) -> SemesterHistorySchema:
    """
    Get student's training history for a specific semester.
    """
    if not is_student(user) or user.id != student_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You cannot access another student's history",
        )

    try:
        semester = Semester.objects.get(pk=semester_id)
    except Semester.DoesNotExist:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Semester not found",
        )

    student = user.student_or_none
    from django.db.models import BooleanField, IntegerField, F, Value, Case, When, CharField
    from django.db.models.functions import Concat
    from sport.models import Attendance, SelfSportReport, Reference

    VTrue = Value(True, output_field=BooleanField())
    VFalse = Value(False, output_field=BooleanField())
    att = (
        Attendance.objects.filter(training__group__semester=semester, student=student)
        .annotate(
            group=F("training__group__name"),
            group_id=F("training__group_id"),
            custom_name=F("training__custom_name"),
            timestamp=Case(
                When(cause_report__isnull=False, then=F("cause_report__uploaded")),
                When(cause_reference__isnull=False, then=F("cause_reference__uploaded")),
                default=F("training__start"),
            ),
            approved=Case(When(hours__gt=0, then=VTrue), default=VFalse),
        )
        .values("group_id", "group", "custom_name", "timestamp", "hours", "approved")
    )
    self_qs = (
        SelfSportReport.objects.filter(
            semester=semester, student=student, attendance=None
        )
        .annotate(
            group=Value("Self training", output_field=CharField()),
            group_id=Value(-1, output_field=IntegerField()),
            custom_name=Concat(
                Value("[Self] ", output_field=CharField()), F("training_type__name")
            ),
            timestamp=F("uploaded"),
            approved=F("approval"),
        )
        .values("group_id", "group", "custom_name", "timestamp", "hours", "approved")
    )
    ref_qs = (
        Reference.objects.filter(semester=semester, student=student, attendance=None)
        .annotate(
            group=Value("Medical leave", output_field=CharField()),
            group_id=Value(-1, output_field=IntegerField()),
            custom_name=Value(None, output_field=CharField()),
            timestamp=F("uploaded"),
            approved=F("approval"),
        )
        .values("group_id", "group", "custom_name", "timestamp", "hours", "approved")
    )

    trainings: list[TrainingHistorySchema] = []
    for row in att.union(self_qs).union(ref_qs).order_by("timestamp"):
        training = TrainingHistoryRowSchema.model_validate(row)
        group_name = (
            training.group
            if training.group_id < 0
            else Group.objects.get(pk=training.group_id).to_frontend_name()
        )
        trainings.append(
            TrainingHistorySchema(
                training_id=-1,
                date=training.timestamp.strftime("%Y-%m-%d"),
                time=training.timestamp.strftime("%H:%M"),
                hours=training.hours,
                group_name=group_name,
                sport_name="Unknown",
                training_class="",
                custom_name=training.custom_name or "",
            )
        )

    sessions = list(
        FitnessTestSession.objects.filter(semester=semester)
        .select_related("semester")
        .order_by("-date", "-id")
    )
    by_session_id: dict[int, list[FitnessTestResult]] = defaultdict(list)
    if sessions:
        results = (
            FitnessTestResult.objects.filter(student=student, session__in=sessions)
            .select_related("exercise")
            .order_by("-session__date", "exercise__id")
        )
        for result in results:
            by_session_id[result.session_id].append(result)

    ongoing_semester_id = get_current_semester().id if sessions else None
    fitness_tests = [
        build_fitness_test_session_result(
            session, by_session_id[session.id], student, ongoing_semester_id
        )
        for session in sessions
    ]

    total_hours = sum(t.hours for t in trainings)

    return SemesterHistorySchema(
        semester_id=semester.id,
        semester_name=str(semester),
        semester_start=semester.start,
        semester_end=semester.end,
        required_hours=semester.hours,
        total_hours=total_hours,
        trainings=trainings,
        fitness_tests=fitness_tests,
    )


@router.get(
    "/students/{student_id}/semester-history",
    responses={
        200: {"description": "Get student semester history"},
    },
)
def get_student_all_semesters_history(
    user: VerifiedDep,
    student_id: int,
) -> list[SemesterHistorySchema]:
    """
    Get student's semester history with attended trainings since enrollment + fitness tests.
    """
    if not is_student(user) or user.id != student_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You cannot access another student's history",
        )

    student = user.student_or_none
    from django.db.models import Q, Sum
    from sport.models import Attendance

    semesters = Semester.objects.filter(
        start__year__gte=student.enrollment_year
    ).exclude(
        Q(start__year=student.enrollment_year) & Q(start__month__lte=7)
    ).order_by("start")

    history: list[SemesterHistorySchema] = []
    for semester in semesters:
        attendances = (
            Attendance.objects.filter(
                student=student, training__group__semester=semester
            )
            .select_related(
                "training",
                "training__group",
                "training__group__sport",
                "training__training_class",
            )
            .annotate(
                training_date=F("training__start"),
                group_name=F("training__group__name"),
                sport_name=F("training__group__sport__name"),
                training_class_name=F("training__training_class__name"),
                custom_name=F("training__custom_name"),
            )
            .order_by("training__start")
        )
        total_hours = attendances.aggregate(total=Sum("hours"))["total"] or 0
        trainings = [
            TrainingHistorySchema(
                training_id=attendance.training.id,
                date=attendance.training_date.strftime("%Y-%m-%d"),
                time=attendance.training_date.strftime("%H:%M"),
                hours=attendance.hours,
                group_name=attendance.group_name,
                sport_name=attendance.sport_name,
                training_class=attendance.training_class_name or "",
                custom_name=attendance.custom_name or "",
            )
            for attendance in attendances
        ]
        history.append(
            SemesterHistorySchema(
                semester_id=semester.id,
                semester_name=semester.name,
                semester_start=semester.start,
                semester_end=semester.end,
                required_hours=semester.hours,
                total_hours=total_hours,
                trainings=trainings,
                fitness_tests=[],
            )
        )

    semester_ids = [semester.semester_id for semester in history]

    sessions = list(
        FitnessTestSession.objects.filter(semester_id__in=semester_ids)
        .select_related("semester")
        .order_by("semester_id", "-date", "-id")
    )
    by_session_id: dict[int, list[FitnessTestResult]] = defaultdict(list)
    if sessions:
        results = (
            FitnessTestResult.objects.filter(student=student, session__in=sessions)
            .select_related("exercise")
            .order_by("session__semester_id", "-session__date", "exercise__id")
        )
        for fitness_result in results:
            by_session_id[fitness_result.session_id].append(fitness_result)

    ongoing_semester_id = get_current_semester().id if sessions else None
    fitness_by_semester: dict[int, list[FitnessTestStudentSessionResultSchema]] = defaultdict(list)
    for session in sessions:
        fitness_by_semester[session.semester_id].append(
            build_fitness_test_session_result(
                session, by_session_id[session.id], student, ongoing_semester_id
            )
        )

    for semester in history:
        semester.fitness_tests = fitness_by_semester[semester.semester_id]

    return history


def get_grading_scheme(student: Student, result: FitnessTestResult):
    return FitnessTestGrading.objects.filter(Q(gender__exact=-1) | Q(gender__exact=student.gender),
                                             exercise=result.exercise)


def get_score(student: Student, result: FitnessTestResult):
    return get_grading_scheme(student, result).get(start_range__lte=result.value, end_range__gt=result.value).score


def get_max_score(student: Student, result: FitnessTestResult):
    return max(map(lambda x: x[0], get_grading_scheme(student, result).values_list('score')))
