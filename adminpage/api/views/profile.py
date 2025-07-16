from django.shortcuts import get_object_or_404
from django.utils import timezone
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response

from api.crud.crud_attendance import (
    get_detailed_hours, get_detailed_hours_and_self, get_student_hours,
    get_student_semester_history
)
from api.permissions import (
    IsStudent, IsStaff,
)
from api.serializers import (
    get_error_serializer,
    EmptySerializer,
)
from api.serializers.profile import GenderSerializer, TrainingHourSerializer, SemesterHistorySerializer
from api.serializers.student import StudentSerializer
from sport.models import Semester, Student, Group


@extend_schema(
    methods=["GET"],
    tags=["Profile"],
    summary="Get student profile information",
    description="Retrieve current student's profile information including personal details, medical group, sport hours statistics, and required hours threshold for the current semester.",
    responses={
        status.HTTP_200_OK: StudentSerializer(),
    }
)
@api_view(["GET"])
@permission_classes([IsStudent])
def get_student_info(request, **kwargs):
    """
    Get info about current student.
    """
    student: Student = request.user.student
    
    # Get student hours data
    hours_data = get_student_hours(student.user.id)
    ongoing_semester = hours_data['ongoing_semester']
    
    # Prepare data for serializer
    serializer = StudentSerializer(student)
    response_data = serializer.data
    
    # Add hours data
    response_data['hours'] = ongoing_semester['hours_not_self']  # Hours for semester (not self-sport)
    response_data['debt'] = ongoing_semester['debt']  # Debt hours
    response_data['self_sport_hours'] = (ongoing_semester['hours_self_not_debt'] + 
                                        ongoing_semester['hours_self_debt'])  # Self sport hours
    response_data['required_hours'] = ongoing_semester['hours_sem_max']  # Required hours threshold for current semester
    
    return Response(response_data)


training_history404 = get_error_serializer(
    "training_history",
    error_code=404,
    error_description="Not found",
)


@extend_schema(
    methods=["GET"],
    tags=["Profile"],
    summary="Get student training history",
    description="Retrieve student's training history for a specific semester, including regular trainings, self-sport activities, and medical references.",
    responses={
        status.HTTP_200_OK: TrainingHourSerializer(many=True),
        status.HTTP_404_NOT_FOUND: training_history404,
    }
)
@api_view(["GET"])
@permission_classes([IsStudent])
def get_history_with_self(request, semester_id: int, **kwargs):
    """
    Get student's trainings per_semester
    """
    semester = get_object_or_404(Semester, pk=semester_id)
    student = request.user  # user.pk == user.student.pk
    return Response(list(map(
            lambda g: {
                **g,
                "group": g["group"] if g["group_id"] < 0 else Group.objects.get(pk=g["group_id"]).to_frontend_name(),
                "timestamp": timezone.localtime(g["timestamp"]).strftime("%b %d %H:%M"),
            },
            get_detailed_hours_and_self(student, semester)
        ))
    )


@extend_schema(
    methods=["GET"],
    tags=["Profile"],
    summary="Get student semester history",
    description="Retrieve student's semester history with attended trainings since enrollment. Returns all semesters with trainings, dates, and hours earned.",
    responses={
        status.HTTP_200_OK: SemesterHistorySerializer(many=True),
    }
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
