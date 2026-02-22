from django.db import transaction
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response

from api_v2.crud import get_group_info, get_sports
from api_v2.crud.crud_groups import get_sports_with_groups
from api_v2.permissions import IsStudent, IsTrainer, IsStaff, IsSuperUser
from api_v2.serializers import (
    GroupInfoSerializer,
    NotFoundSerializer,
)
from api_v2.serializers.group import DetailedSportSerializer
from sport.models import Group, Schedule, Student, Sport


@extend_schema(
    methods=["GET"],
    tags=["For any user"],
    summary="Get sport group information",
    description="Retrieve detailed information about a sport group including schedule, capacity, enrolled students, and enrollment status.",
    responses={
        status.HTTP_200_OK: GroupInfoSerializer,
        status.HTTP_404_NOT_FOUND: NotFoundSerializer,
    },
)
@api_view(["GET"])
@permission_classes([IsStudent | IsTrainer | IsStaff | IsSuperUser])
def group_info_view(request, group_id, **kwargs):
    get_object_or_404(Group, pk=group_id)
    group_info = get_group_info(group_id)
    print(group_info)
    return Response(GroupInfoSerializer(group_info).data)


@extend_schema(
    methods=["GET"],
    tags=["For any user"],
    summary="Get available clubs with detailed groups information",
    description="Retrieve list of all available clubs with their groups, schedules, trainers, capacity, and enrollment information.",
    responses={
        status.HTTP_200_OK: DetailedSportSerializer(many=True),
        status.HTTP_404_NOT_FOUND: NotFoundSerializer,
    },
)
@api_view(["GET"])
@permission_classes([IsStudent | IsStaff | IsTrainer])
def sports_view(request, **kwargs):
    # Get student if authenticated
    student = None
    if hasattr(request.user, "student"):
        student = request.user.student

    sports_data = get_sports_with_groups(student)
    serializer = DetailedSportSerializer(sports_data, many=True)
    return Response(serializer.data)
