from django.shortcuts import get_object_or_404
from django.utils import timezone
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response

from api_v2.crud.crud_attendance import (
    get_detailed_hours,
    get_detailed_hours_and_self,
    get_student_hours,
    get_student_all_semesters_history_crud,
)
from api_v2.crud.crud_fitness_test import (
    get_student_fitness_results_for_semester_crud,
    get_student_fitness_results_for_all_semesters_crud,
)
from api_v2.permissions import (
    IsStudent,
    IsStaff,
    IsTrainer,
)
from api_v2.serializers import (
    get_error_serializer,
    EmptySerializer,
)
from api_v2.serializers.profile import (
    GenderSerializer,
    TrainingHourSerializer,
    SemesterHistorySerializer,
    StudentSpecificSemesterHistorySerializer,
    SemesterHistoryWithFitnessSerializer,
)
from api_v2.serializers.student import UserSerializer
from sport.models import Semester, Student, Group


@extend_schema(
    methods=["GET"],
    tags=["For any user"],
    summary="Get user profile information",
    description="Retrieve current user's profile information including user ID, statuses, and detailed information for each status.",
    responses={status.HTTP_200_OK: UserSerializer},
)
@api_view(["GET"])
@permission_classes([IsStudent | IsStaff | IsTrainer])
def get_user_info(request, **kwargs):
    serializer = UserSerializer(request.user, context={"request": request})
    return Response(serializer.data, status=status.HTTP_200_OK)


training_history404 = get_error_serializer(
    "training_history",
    error_code=404,
    error_description="Not found",
)


@extend_schema(
    methods=["GET"],
    tags=["For student"],
    summary="Get student training history",
    description="Retrieve student's training history for a specific semester, including trainings, self-sport activities, results of fitness tests, and medical references.",
    responses={
        status.HTTP_200_OK: SemesterHistoryWithFitnessSerializer,
        status.HTTP_404_NOT_FOUND: training_history404,
    },
)
@api_view(["GET"])
@permission_classes([IsStudent])
def get_student_specific_semester_history(request, semester_id: int, **kwargs):
    """
    Get student's training history for a specific semester using unified logic.
    """
    student: Student = request.user.student
    semester = get_object_or_404(Semester, pk=semester_id)

    trainings_queryset = get_detailed_hours_and_self(student, semester)
    trainings = []
    for t in get_detailed_hours_and_self(student, semester):
        trainings.append({
            "training_id": t.get("id", -1),
            "date": t["timestamp"].strftime("%Y-%m-%d"),
            "time": t["timestamp"].strftime("%H:%M"),
            "hours": t.get("hours", 0),
            "group_name": t["group"] if t.get("group_id", -1) < 0 else Group.objects.get(pk=t["group_id"]).to_frontend_name(),
            "sport_name": t.get("sport_name", "Unknown"),
            "training_class": t.get("training_class", ""),
            "custom_name": t.get("custom_name", ""),
        })


    fitness_tests = get_student_fitness_results_for_semester_crud(
        student=student,
        semester=semester,
        latest_only=False,
    )

    semester_payload = {
        "semester_id": semester.id,
        "semester_name": str(semester),
        "semester_start": semester.start,
        "semester_end": semester.end,
        "required_hours": semester.hours,
        "total_hours": sum(t["hours"] for t in trainings),
        "trainings": trainings,
        "fitness_tests": fitness_tests,
    }

    serializer = SemesterHistoryWithFitnessSerializer(semester_payload)
    return Response(serializer.data)




@extend_schema(
    methods=["GET"],
    tags=["For student"],
    summary="Get student semester history",
    description="Retrieve student's semester history with attended trainings and fitness tests since enrollment. Returns all semesters with trainings, dates, hours earned and results of fitness tests.",
    responses={
        status.HTTP_200_OK: SemesterHistoryWithFitnessSerializer(many=True),
    },
)
@api_view(["GET"])
@permission_classes([IsStudent])
def get_student_all_semesters_history(request, **kwargs):
    """
    Get student's semester history with attended trainings since enrollment + fitness tests
    """
    student: Student = request.user.student
    history = get_student_all_semesters_history_crud(student)

    semester_ids = [h["semester_id"] for h in history]
    fitness_by_semester = get_student_fitness_results_for_all_semesters_crud(
        student=student,
        semester_ids=semester_ids,
        latest_only=False,
    )

    for h in history:
        h["fitness_tests"] = fitness_by_semester.get(h["semester_id"], [])

    return Response(SemesterHistoryWithFitnessSerializer(history, many=True).data)
