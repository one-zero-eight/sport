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
    get_student_semester_history,
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
    description="Retrieve student's training history for a specific semester, including regular trainings, self-sport activities, results of fitness test, and medical references.",
    responses={
        status.HTTP_200_OK: TrainingHourSerializer(many=True),
        status.HTTP_404_NOT_FOUND: training_history404,
    },
)
@api_view(["GET"])
@permission_classes([IsStudent])
def get_history_with_self(request, semester_id: int, **kwargs):
    """
    Get student's trainings per_semester
    """
    semester = get_object_or_404(Semester, pk=semester_id)
    student = request.user  # user.pk == user.student.pk
    return Response(
        list(
            map(
                lambda g: {
                    **g,
                    "group": g["group"]
                    if g["group_id"] < 0
                    else Group.objects.get(pk=g["group_id"]).to_frontend_name(),
                    "timestamp": timezone.localtime(g["timestamp"]).strftime(
                        "%b %d %H:%M"
                    ),
                },
                get_detailed_hours_and_self(student, semester),
            )
        )
    )


@extend_schema(
    methods=["GET"],
    tags=["For student"],
    summary="Get student semester history",
    description="Retrieve student's semester history with attended trainings and fitness tests since enrollment. Returns all semesters with trainings, dates, hours earned and results of fitness tests.",
    responses={
        status.HTTP_200_OK: SemesterHistorySerializer(many=True),
    },
)
@api_view(["GET"])
@permission_classes([IsStudent])
def get_student_semester_history_view(request, **kwargs):
    """
    Get student's semester history with attended trainings since enrollment
    """
    student: Student = request.user.student
    history = get_student_semester_history(student)
    return Response(history)
