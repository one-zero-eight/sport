from django.db import transaction
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response

from api.crud import get_group_info, get_sports
from api.permissions import IsStudent, IsTrainer
from api.serializers import GroupInfoSerializer, NotFoundSerializer, SportsSerializer, EmptySerializer, ErrorSerializer
from api.serializers.group import SportEnrollSerializer
from sport.models import Group, Schedule, Student, Sport


@extend_schema(
    methods=["GET"],
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
    responses={
        status.HTTP_200_OK: SportsSerializer,
        status.HTTP_404_NOT_FOUND: NotFoundSerializer,
    }
)
@api_view(["GET"])
# @permission_classes([IsStudent]) Temporary off for academic_leave students
def sports_view(request, **kwargs):
    serializer = SportsSerializer({'sports': get_sports()})
    return Response(serializer.data)


@extend_schema(
    methods=["POST"],
    request=SportEnrollSerializer,
    responses={
        status.HTTP_200_OK: EmptySerializer,
        status.HTTP_404_NOT_FOUND: NotFoundSerializer,
        status.HTTP_400_BAD_REQUEST: ErrorSerializer,
    },
)
@api_view(["POST"])
@permission_classes([IsStudent])
@transaction.atomic
def select_sport(request, **kwargs):
    serializer = SportEnrollSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    sport = get_object_or_404(
        Sport,
        pk=serializer.validated_data["sport_id"]
    )

    student: Student = request.user.student
    student.sport = sport
    student.save()

    return Response({})
