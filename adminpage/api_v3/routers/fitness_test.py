from collections import defaultdict
import datetime
from typing import Any

from django.db.models import Q
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field, field_validator
from starlette import status

from api_v3.dependencies import VerifiedDep
from api_v3.permissions import is_admin, is_trainer
from api_v3.utils.search import search_students
from api_v3.utils.semester import get_current_semester

from sport.models import (
    FitnessTestSession,
    FitnessTestResult,
    FitnessTestExercise,
    Semester,
)

router = APIRouter(
    tags=["Fitness test"],
    responses={
        401: {"description": "Invalid token"},
        403: {"description": "Unauthorized"},
    },
)


class FitnessTestExerciseSchema(BaseModel):
    id: int
    name: str = Field(validation_alias="exercise_name")
    unit: str | None = Field(default=None, validation_alias="value_unit")
    threshold: float | int | None = None
    select: list[str] = Field(default_factory=list)

    @field_validator("select", mode="before")
    @classmethod
    def split_select(cls, v: Any) -> list[str]:
        if v is None:
            return []
        if isinstance(v, list):
            return [str(x) for x in v]
        if isinstance(v, str):
            return [s for s in v.split(",") if s]
        return []


class FitnessTestSessionSchema(BaseModel):
    id: int
    semester_id: int
    retake: bool
    date: datetime.datetime
    teacher: str

    @field_validator("teacher", mode="before")
    @classmethod
    def teacher_to_str(cls, v: Any) -> str:
        if v is None:
            return ""
        if isinstance(v, str):
            return v
        return str(v)


class FitnessTestStudentExerciseResultSchema(BaseModel):
    exercise_id: int
    exercise_name: str
    unit: str | None
    value: str


class FitnessTestStudentInfoSchema(BaseModel):
    user_id: int
    email: str
    first_name: str
    last_name: str


class FitnessTestStudentGroupedResultSchema(BaseModel):
    student: FitnessTestStudentInfoSchema
    exercise_results: list[FitnessTestStudentExerciseResultSchema]


class FitnessTestSessionWithGroupedResultsSchema(BaseModel):
    session: FitnessTestSessionSchema
    exercises: list[FitnessTestExerciseSchema]
    results: dict[int, FitnessTestStudentGroupedResultSchema]


class FitnessTestUpdateEntrySchema(BaseModel):
    student_id: int
    exercise_id: int
    value: str


class FitnessTestUploadSchema(BaseModel):
    semester_id: int
    retake: bool
    results: list[FitnessTestUpdateEntrySchema]


class PostStudentExerciseResultSchema(BaseModel):
    result: str = "ok"
    session_id: int


class SuggestionSchema(BaseModel):
    id: int
    first_name: str
    last_name: str
    email: str


@router.get(
    "/fitness-test/exercises",
    responses={
        200: {"description": "Get fitness test exercises"},
    },
)
def get_exercises(
    user: VerifiedDep,
    semester_id: int | None = Query(
        None,
        description="Semester ID; if omitted, current semester is used if available",
    ),
) -> list[FitnessTestExerciseSchema]:
    """
    Get all fitness test exercises for a specific semester.
    """
    if semester_id is None:  # Set current semester
        semester = get_current_semester()
        semester_id = semester.id

    exercises = FitnessTestExercise.objects.filter(semester=semester_id)
    return [
        FitnessTestExerciseSchema.model_validate(e, from_attributes=True)
        for e in exercises
    ]


@router.get(
    "/fitness-test/sessions",
    responses={
        200: {"description": "Get fitness test sessions"},
    },
)
def get_sessions(
    user: VerifiedDep,
    semester_id: int | None = Query(
        None,
        description="Semester ID; if omitted, all sessions are returned",
    ),
) -> list[FitnessTestSessionSchema]:
    """
    Get all fitness test sessions for a specific semester or all.
    """
    if not (is_trainer(user) or is_admin(user)):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not allowed to view fitness test sessions",
        )

    if semester_id is None:
        sessions = FitnessTestSession.objects.all()
    else:
        sessions = FitnessTestSession.objects.filter(semester_id=semester_id)

    return [
        FitnessTestSessionSchema.model_validate(s, from_attributes=True)
        for s in sessions
    ]


@router.get(
    "/fitness-test/sessions/{session_id}",
    responses={
        200: {"description": "Get fitness test session results"},
        404: {"description": "No results found"},
    },
)
def get_fitness_test_session(
    user: VerifiedDep,
    session_id: int,
) -> FitnessTestSessionWithGroupedResultsSchema:
    """
    Get grouped fitness test results for a session.
    """
    if not (is_trainer(user) or is_admin(user)):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not allowed to view fitness test results",
        )

    results_qs = FitnessTestResult.objects.filter(
        session_id=session_id
    ).select_related("student__user", "exercise")
    if not results_qs.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No results found",
        )

    student_results: dict[int, list[FitnessTestStudentExerciseResultSchema]] = defaultdict(list)
    for result in results_qs:
        sid = result.student.user.id
        student_results[sid].append(
            FitnessTestStudentExerciseResultSchema(
                exercise_id=result.exercise.id,
                exercise_name=result.exercise.exercise_name,
                unit=result.exercise.value_unit,
                value=result.value,
            )
        )

    results_dict: dict[int, FitnessTestStudentGroupedResultSchema] = {}
    for sid, exercise_results in student_results.items():
        student_result = next(r for r in results_qs if r.student.user.id == sid)
        student_info = FitnessTestStudentInfoSchema(
            user_id=student_result.student.user.id,
            email=student_result.student.user.email,
            first_name=student_result.student.user.first_name,
            last_name=student_result.student.user.last_name,
        )
        results_dict[sid] = FitnessTestStudentGroupedResultSchema(
            student=student_info,
            exercise_results=exercise_results,
        )

    try:
        session = FitnessTestSession.objects.get(id=session_id)
    except FitnessTestSession.DoesNotExist:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found",
        )

    exercises = FitnessTestExercise.objects.filter(
        id__in=FitnessTestResult.objects.filter(session_id=session_id)
        .values_list("exercise")
        .distinct()
    )

    return FitnessTestSessionWithGroupedResultsSchema(
        session=FitnessTestSessionSchema.model_validate(
            session, from_attributes=True
        ),
        exercises=[
            FitnessTestExerciseSchema.model_validate(e, from_attributes=True)
            for e in exercises
        ],
        results=results_dict,
    )


@router.post(
    "/fitness-test/sessions/{session_id}",
    responses={
        201: {"description": "Upload or update student fitness test results"},
        400: {"description": "Invalid data"},
        404: {"description": "Not found"},
    },
)
def upload_fitness_test_results(
    user: VerifiedDep,
    session_id: int,
    body: FitnessTestUploadSchema,
) -> PostStudentExerciseResultSchema:
    """
    Upload or update student fitness test results.
    """
    if not is_admin(user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not allowed to change fitness test results",
        )

    if session_id != 0:
        try:
            existing_session = FitnessTestSession.objects.get(id=session_id)
            semester = existing_session.semester
        except FitnessTestSession.DoesNotExist:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No fitness test session with id={session_id}",
            )
    else:
        semester_id = body.semester_id
        try:
            semester = Semester.objects.get(id=semester_id)
        except Semester.DoesNotExist:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No semester with id={semester_id}",
            )

    results = [
        {"student_id": r.student_id, "exercise_id": r.exercise_id, "value": r.value}
        for r in body.results
    ]

    try:
        import logging

        logger = logging.getLogger(__name__)
        from sport.models import Student

        session, created = FitnessTestSession.objects.get_or_create(
            id=session_id,
            defaults={
                "semester": semester,
                "teacher_id": user.id,
                "retake": body.retake,
                "date": datetime.datetime.now(),
            },
        )

        errors = []
        for res in results:
            logger.info(
                f"Processing result: student_id={res['student_id']}, "
                f"exercise_id={res['exercise_id']}, value={res['value']}"
            )
            try:
                student = Student.objects.get(user__id=res["student_id"])
            except Student.DoesNotExist:
                errors.append(
                    f"Student with user_id={res['student_id']} does not exist"
                )
                continue

            try:
                exercise = FitnessTestExercise.objects.get(id=res["exercise_id"])
            except FitnessTestExercise.DoesNotExist:
                errors.append(
                    f"Exercise with id={res['exercise_id']} does not exist"
                )
                continue

            FitnessTestResult.objects.update_or_create(
                exercise=exercise,
                student=student,
                defaults={"value": res["value"]},
                session=session,
            )

        if errors:
            raise ValueError("; ".join(errors))

        session_pk = session.id
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )

    return PostStudentExerciseResultSchema(session_id=session_pk)


@router.get(
    "/fitness-test/suggest-student",
    responses={
        200: {"description": "Suggest students for fitness test"},
    },
)
def suggest_fitness_test_student(
    user: VerifiedDep,
    term: str = Query(..., description="Search term"),
) -> list[SuggestionSchema]:
    """
    Suggest students based on a search term for fitness test.
    """
    if not (is_trainer(user) or is_admin(user)):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not allowed to suggest students",
        )

    suggested_students = search_students(
        term,
        requirement=~Q(fitnesstestresult__exercise__semester=get_current_semester()),
    )
    return [
        SuggestionSchema(
            id=s["id"],
            first_name=s["first_name"],
            last_name=s["last_name"],
            email=s["email"],
        )
        for s in suggested_students
    ]

