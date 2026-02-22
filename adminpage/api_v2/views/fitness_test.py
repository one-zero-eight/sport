import logging
from collections import defaultdict
from drf_spectacular.utils import extend_schema_view
from django.db.models import Q
from drf_spectacular.utils import extend_schema
from rest_framework import status, serializers
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response

from api_v2.permissions import (
    IsStaff,
    IsTrainer,
    IsStudent,
    IsSuperUser,
)
from api_v2.serializers import (
    NotFoundSerializer,
    ErrorSerializer,
    SuggestionSerializer,
)

from api_v2.crud import (
    get_exercises_crud,
    post_student_exercises_result_crud,
    get_email_name_like_students,
    get_current_semester_crud,
)
from api_v2.serializers.attendance import SuggestionQueryFTSerializer
from api_v2.serializers.fitness_test import (
    FitnessTestExerciseSerializer,
    FitnessTestSessionSerializer,
    FitnessTestUpload,
    FitnessTestSessionWithGroupedResults,
)
from api_v2.serializers.semester import SemesterInSerializer
from api_v2.serializers.fitness_test import PostStudentExerciseResult
from sport.models import (
    FitnessTestSession,
    FitnessTestResult,
    FitnessTestExercise,
    Semester,
    Student,
)

logger = logging.getLogger(__name__)


@extend_schema(
    methods=["GET"],
    tags=["For teacher"],
    summary="Get fitness test exercises",
    description="Get all fitness test exercises for a specific semester. If semester_id is not provided, returns exercises for the current semester.",
    parameters=[SemesterInSerializer],
    responses={
        status.HTTP_200_OK: FitnessTestExerciseSerializer(many=True),
    },
)
@api_view(["GET"])
@permission_classes([IsTrainer | IsStaff])
def get_exercises(request, **kwargs):
    serializer = SemesterInSerializer(data=request.GET)
    serializer.is_valid(raise_exception=True)
    semester_id = serializer.validated_data.get("semester_id")

    if semester_id is None:
        semester_id = get_current_semester_crud()
    exercises = get_exercises_crud(semester_id)

    return Response(FitnessTestExerciseSerializer(exercises, many=True).data)


@extend_schema(
    methods=["GET"],
    tags=["For teacher"],
    summary="Get fitness test sessions",
    description="Get all fitness test sessions for a specific semester. If semester_id is not provided, returns all sessions. Only accessible by trainers.",
    parameters=[SemesterInSerializer],
    responses={status.HTTP_200_OK: FitnessTestSessionSerializer(many=True)},
)
@api_view(["GET"])
@permission_classes([IsTrainer | IsSuperUser | IsStaff])
def get_sessions(request, **kwargs):
    serializer = SemesterInSerializer(data=request.GET)
    serializer.is_valid(raise_exception=True)
    semester_id = serializer.validated_data.get("semester_id")

    if semester_id is None:
        sessions = FitnessTestSession.objects.all()
    else:
        sessions = FitnessTestSession.objects.filter(semester_id=semester_id)

    return Response(FitnessTestSessionSerializer(sessions, many=True).data)


@extend_schema_view(
    get=extend_schema(
        tags=["For teacher"],
        summary="Get fitness test session results",
        description="",
        responses={
            status.HTTP_200_OK: FitnessTestSessionWithGroupedResults(),
            status.HTTP_404_NOT_FOUND: NotFoundSerializer(),
        },
    ),
    post=extend_schema(
        tags=["For teacher"],
        summary="Upload or update student fitness test results",
        description="",
        request=FitnessTestUpload,
        responses={
            status.HTTP_201_CREATED: PostStudentExerciseResult(),
            status.HTTP_400_BAD_REQUEST: ErrorSerializer(),
            status.HTTP_404_NOT_FOUND: NotFoundSerializer(),
        },
    ),
)
@api_view(["GET", "POST"])
@permission_classes([IsTrainer | IsSuperUser | IsStaff])
def fitness_test_session_view(request, session_id: int, **kwargs):
    if request.method == "GET":
        results = FitnessTestResult.objects.filter(
            session_id=session_id
        ).select_related("student__user", "exercise")
        if not results.exists():
            return Response(
                status=status.HTTP_404_NOT_FOUND,
                data=NotFoundSerializer({"detail": "No results found"}).data,
            )

        student_results = defaultdict(list)
        for result in results:
            sid = result.student.user.id
            student_results[sid].append(
                {
                    "exercise_id": result.exercise.id,
                    "exercise_name": result.exercise.exercise_name,
                    "unit": result.exercise.value_unit,
                    "value": result.value,
                }
            )

        results_dict = {}
        for sid, exercise_results in student_results.items():
            student_result = next(r for r in results if r.student.user.id == sid)
            results_dict[sid] = {
                "student": student_result.student,
                "exercise_results": exercise_results,
            }

        payload = {
            "session": FitnessTestSession.objects.get(id=session_id),
            "exercises": FitnessTestExercise.objects.filter(
                id__in=FitnessTestResult.objects.filter(session_id=session_id)
                .values_list("exercise")
                .distinct()
            ),
            "results": results_dict,
        }
        return Response(
            FitnessTestSessionWithGroupedResults(payload).data,
            status=status.HTTP_200_OK,
        )

    trainer = request.user
    if not trainer.is_superuser and not trainer.has_perm("sport.change_fitness_test"):
        return Response(status=status.HTTP_400_BAD_REQUEST)

    serializer = FitnessTestUpload(data=request.data)
    serializer.is_valid(raise_exception=True)

    if session_id and session_id != "new":
        try:
            existing_session = FitnessTestSession.objects.get(id=session_id)
            semester = existing_session.semester
        except FitnessTestSession.DoesNotExist:
            return Response(
                status=status.HTTP_404_NOT_FOUND,
                data=NotFoundSerializer(
                    {"detail": f"No fitness test session with id={session_id}"}
                ).data,
            )
    else:
        semester_id = serializer.validated_data["semester_id"]
        try:
            semester = Semester.objects.get(id=semester_id)
        except Semester.DoesNotExist:
            return Response(
                status=status.HTTP_404_NOT_FOUND,
                data=NotFoundSerializer(
                    {"detail": f"No semester with id={semester_id}"}
                ).data,
            )

    retake = serializer.validated_data["retake"]
    results = serializer.validated_data["results"]

    try:
        session = post_student_exercises_result_crud(
            semester, retake, results, session_id, request.user
        )
    except ValueError as e:
        logger.error(f"Error in fitness test upload: {e}")
        return Response(
            status=status.HTTP_400_BAD_REQUEST,
            data=ErrorSerializer({"detail": str(e)}).data,
        )

    return Response(
        PostStudentExerciseResult({"session_id": session}).data,
        status=status.HTTP_201_CREATED,
    )


@extend_schema(
    methods=["GET"],
    tags=["For teacher"],
    summary="Suggest students for fitness test",
    description="Suggest students based on a search term for fitness test. Only accessible by trainers.",
    parameters=[SuggestionQueryFTSerializer],
    responses={
        status.HTTP_200_OK: SuggestionSerializer(many=True),
    },
)
@api_view(["GET"])
@permission_classes([IsTrainer | IsSuperUser | IsStaff])
def suggest_fitness_test_student(request, **kwargs):
    serializer = SuggestionQueryFTSerializer(data=request.GET)
    serializer.is_valid(raise_exception=True)

    suggested_students = get_email_name_like_students(
        serializer.validated_data["term"],
        requirement=(
            ~Q(fitnesstestresult__exercise__semester=get_current_semester_crud())
        ),
    )
    return Response(
        SuggestionSerializer(suggested_students, many=True).data)
