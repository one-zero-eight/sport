from django.db import transaction
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response

from api.crud import get_group_info, get_sports
from api.crud.crud_groups import get_sports_with_groups
from api.permissions import IsStudent, IsTrainer
from api.serializers import GroupInfoSerializer, NotFoundSerializer, SportsSerializer, EmptySerializer, ErrorSerializer
from api.serializers.group import SportsWithGroupsSerializer, DetailedSportSerializer
from sport.models import Group, Schedule, Student, Sport


@extend_schema(
    methods=["GET"],
    tags=["Groups"],
    summary="Get sport group information",
    description="Retrieve detailed information about a sport group including schedule, capacity, enrolled students, and enrollment status.",
    responses={
        status.HTTP_200_OK: GroupInfoSerializer,
        status.HTTP_404_NOT_FOUND: NotFoundSerializer,
    }
)
@api_view(["GET"])
@permission_classes([IsStudent | IsTrainer])
def group_info_view(request, group_id, **kwargs):
    student = request.user  # user.pk == user.student.pk
    get_object_or_404(Group, pk=group_id)
    group_info = get_group_info(group_id, student.student)
    group_schedule = Schedule.objects.filter(group_id=group_id).all()
    group_info.update({"schedule": group_schedule})
    serializer = GroupInfoSerializer(group_info)
    return Response(serializer.data)


@extend_schema(
    methods=["GET"],
    tags=["Clubs"],
    summary="Get available clubs with detailed groups information",
    description="Retrieve list of all available clubs with their groups, schedules, trainers, capacity, and enrollment information.",
    responses={
        status.HTTP_200_OK: DetailedSportSerializer(many=True),
        status.HTTP_404_NOT_FOUND: NotFoundSerializer,
    }
)
@api_view(["GET"])
# @permission_classes([IsStudent]) Temporary off for academic_leave students
def clubs_view(request, **kwargs):
    # Get student if authenticated
    student = None
    if hasattr(request.user, 'student'):
        student = request.user.student
    
    sports_data = get_sports_with_groups(student)
    serializer = DetailedSportSerializer(sports_data, many=True)
    return Response(serializer.data)

