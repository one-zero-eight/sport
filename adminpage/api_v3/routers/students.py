from typing import Any

from django.db.models import F
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from starlette import status

from api_v3.dependencies import VerifiedDep
from api_v3.permissions import is_student
from api_v3.routers.fitness_test import FitnessTestSessionSchema
from sport.models import Semester, Group


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


class FitnessTestExerciseResultSchema(BaseModel):
    exercise_id: int
    exercise_name: str
    unit: str | None
    value: str


class FitnessTestStudentSessionResultSchema(BaseModel):
    session: FitnessTestSessionSchema
    exercise_results: list[FitnessTestExerciseResultSchema]


class SemesterHistorySchema(BaseModel):
    semester_id: int
    semester_name: str
    semester_start: Any
    semester_end: Any
    required_hours: int
    total_hours: int
    trainings: list[TrainingHistorySchema]
    fitness_tests: list[FitnessTestStudentSessionResultSchema] | None = None


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
    for t in att.union(self_qs).union(ref_qs).order_by("timestamp"):
        group_name = (
            t["group"]
            if t.get("group_id", -1) < 0
            else Group.objects.get(pk=t["group_id"]).to_frontend_name()
        )
        trainings.append(
            TrainingHistorySchema(
                training_id=t.get("id", -1),
                date=t["timestamp"].strftime("%Y-%m-%d"),
                time=t["timestamp"].strftime("%H:%M"),
                hours=t.get("hours", 0),
                group_name=group_name,
                sport_name=t.get("sport_name", "Unknown"),
                training_class=t.get("training_class", "") or "",
                custom_name=t.get("custom_name", "") or "",
            )
        )

    from collections import defaultdict
    from sport.models import FitnessTestResult, FitnessTestSession

    sessions_qs = (
        FitnessTestSession.objects.filter(semester=semester)
        .select_related("semester")
        .order_by("-date", "-id")
    )
    sessions = list(sessions_qs)

    fitness_tests_raw = []
    if sessions:
        results_qs = (
            FitnessTestResult.objects.filter(student=student, session__in=sessions)
            .select_related("exercise", "session", "session__semester")
            .order_by("-session__date", "exercise__id")
        )

        by_session_id = defaultdict(list)
        for r in results_qs:
            ex = r.exercise
            by_session_id[r.session_id].append(
                {
                    "exercise_id": ex.id,
                    "exercise_name": ex.exercise_name,
                    "unit": ex.value_unit,
                    "value": r.value,
                }
            )

        fitness_tests_raw = [
            {"session": s, "exercise_results": by_session_id.get(s.id, [])}
            for s in sessions
        ]
    fitness_tests: list[FitnessTestStudentSessionResultSchema] = []
    for item in fitness_tests_raw:
        session = FitnessTestSessionSchema.model_validate(
            item["session"], from_attributes=True
        )
        ex_results = [
            FitnessTestExerciseResultSchema(
                exercise_id=e["exercise_id"],
                exercise_name=e["exercise_name"],
                unit=e.get("unit"),
                value=str(e["value"]),
            )
            for e in item.get("exercise_results", [])
        ]
        fitness_tests.append(
            FitnessTestStudentSessionResultSchema(
                session=session,
                exercise_results=ex_results,
            )
        )

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

    history: list[dict[str, Any]] = []
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
        trainings = []
        for attendance in attendances:
            trainings.append(
                {
                    "training_id": attendance.training.id,
                    "date": attendance.training_date.strftime("%Y-%m-%d"),
                    "time": attendance.training_date.strftime("%H:%M"),
                    "hours": attendance.hours,
                    "group_name": attendance.group_name,
                    "sport_name": attendance.sport_name,
                    "training_class": attendance.training_class_name or "",
                    "custom_name": attendance.custom_name or "",
                }
            )
        history.append(
            {
                "semester_id": semester.id,
                "semester_name": semester.name,
                "semester_start": semester.start.strftime("%Y-%m-%d"),
                "semester_end": semester.end.strftime("%Y-%m-%d"),
                "required_hours": semester.hours,
                "total_hours": total_hours,
                "trainings": trainings,
            }
        )

    semester_ids = [h["semester_id"] for h in history]
    from collections import defaultdict
    from sport.models import FitnessTestResult, FitnessTestSession

    sessions_qs = FitnessTestSession.objects.all().select_related("semester")
    if semester_ids is not None:
        sessions_qs = sessions_qs.filter(semester_id__in=semester_ids)
    sessions_qs = sessions_qs.order_by("semester_id", "-date", "-id")
    sessions = list(sessions_qs)

    fitness_by_semester: dict[int, list[dict[str, Any]]] = {}
    if sessions:
        results_qs = (
            FitnessTestResult.objects.filter(student=student, session__in=sessions)
            .select_related("exercise", "session", "session__semester")
            .order_by("session__semester_id", "-session__date", "exercise__id")
        )

        by_session_id = defaultdict(list)
        for r in results_qs:
            ex = r.exercise
            by_session_id[r.session_id].append(
                {
                    "exercise_id": ex.id,
                    "exercise_name": ex.exercise_name,
                    "unit": ex.value_unit,
                    "value": r.value,
                }
            )

        by_semester = defaultdict(list)
        for s in sessions:
            by_semester[s.semester_id].append(
                {"session": s, "exercise_results": by_session_id.get(s.id, [])}
            )
        fitness_by_semester = dict(by_semester)

    result: list[SemesterHistorySchema] = []
    for h in history:
        sem_id = h["semester_id"]
        fitness_tests_raw = fitness_by_semester.get(sem_id, [])

        fitness_tests: list[FitnessTestStudentSessionResultSchema] = []
        for item in fitness_tests_raw:
            session = FitnessTestSessionSchema.model_validate(
                item["session"], from_attributes=True
            )
            ex_results = [
                FitnessTestExerciseResultSchema(
                    exercise_id=e["exercise_id"],
                    exercise_name=e["exercise_name"],
                    unit=e.get("unit"),
                    value=str(e["value"]),
                )
                for e in item.get("exercise_results", [])
            ]
            fitness_tests.append(
                FitnessTestStudentSessionResultSchema(
                    session=session,
                    exercise_results=ex_results,
                )
            )

        trainings = [
            TrainingHistorySchema(
                training_id=t["training_id"],
                date=t["date"],
                time=t["time"],
                hours=t["hours"],
                group_name=t["group_name"],
                sport_name=t["sport_name"],
                training_class=t.get("training_class", "") or "",
                custom_name=t.get("custom_name", "") or "",
            )
            for t in h.get("trainings", [])
        ]

        result.append(
            SemesterHistorySchema(
                semester_id=h["semester_id"],
                semester_name=h["semester_name"],
                semester_start=h["semester_start"],
                semester_end=h["semester_end"],
                required_hours=h["required_hours"],
                total_hours=h["total_hours"],
                trainings=trainings,
                fitness_tests=fitness_tests,
            )
        )

    return result

