from datetime import time

from django.conf import settings
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from django.utils import timezone

from api_v2.crud import (
    get_sport_schedule,
    get_trainings_for_student,
    get_trainings_for_trainer,
)
from api_v2.permissions import IsStaff, IsStudent, IsTrainer
from api_v2.serializers import TrainingInfoSerializer, CalendarRequestSerializer, CalendarPersonalSerializer


def convert_training_schedule(t) -> dict:
    return {
        "title": t["group_name"],
        "daysOfWeek": [(t["weekday"] + 1) % 7],
        "startTime": t["start"],
        "endTime": t["end"],
        "group_id": t["group_id"],
        "training_class": t["training_class"],
        "current_load": t["current_load"],
        "capacity": t["capacity"],
    }


def convert_personal_training(t) -> dict:
    start_time = timezone.localtime(t["start"])
    end_time = timezone.localtime(t["end"])

    return {
        "id": t["id"],
        "title": t["group_name"],
        "start": start_time,
        "end": end_time,
        "group_id": t["group_id"],
        "can_edit": start_time
            <= timezone.localtime()
            <= start_time + settings.TRAINING_EDITABLE_INTERVAL,
        "can_grade": bool(t.get("can_grade", False)),
        "training_class": t.get("training_class", ""),
        "group_accredited": bool(t.get("group_accredited", False)),
        "allDay": start_time.time() == time(0, 0, 0)
            and end_time.time() == time(23, 59, 59),
        "can_check_in": bool(t.get("can_check_in", False)),
        "checked_in": bool(t.get("checked_in", False)),
    }



@extend_schema(
    methods=["GET"],
    tags=["For any user"],
    summary="Get sport schedule",
    description="Retrieve training schedule for a specific sport. (Specify sport_id equal to 0 to get all trainings in the specified time period)",
    parameters=[CalendarRequestSerializer],
    responses={
        status.HTTP_200_OK: TrainingInfoSerializer(many=True),
    },
)
@api_view(["GET"])
@permission_classes([IsStudent | IsStaff | IsTrainer])
def get_schedule(request, sport_id, **kwargs):
    serializer = CalendarRequestSerializer(data=request.GET)
    serializer.is_valid(raise_exception=True)
    student = getattr(request.user, "student", None)
    trainings = get_sport_schedule(
        start_time=serializer.validated_data["start"],
        end_time=serializer.validated_data["end"],
        sport_id=sport_id,
        student=student,
    )
    return Response(TrainingInfoSerializer(trainings, many=True).data)


@extend_schema(
    methods=["GET"],
    tags=["For any user"],
    summary="Get personal schedule",
    description="Retrieve personal training schedule for the current user (student or trainer). Shows trainings relevant to the user's role.",
    parameters=[CalendarRequestSerializer],
    responses={status.HTTP_200_OK: CalendarPersonalSerializer(many=True)},
)
@api_view(["GET"])
@permission_classes([IsStudent | IsTrainer | IsStaff])
def get_personal_schedule(request, **kwargs):
    query_serializer = CalendarRequestSerializer(data=request.GET)
    query_serializer.is_valid(raise_exception=True)

    start = query_serializer.validated_data["start"]
    end = query_serializer.validated_data["end"]

    student_trainings = []
    trainer_trainings = []

    if hasattr(request.user, "student"):
        student_trainings = get_trainings_for_student(request.user.student, start, end)

    if hasattr(request.user, "trainer"):
        trainer_trainings = get_trainings_for_trainer(request.user.trainer, start, end)

    trainings_by_id = {}

    for t in trainer_trainings:
        trainings_by_id[t["id"]] = {
            **t,
            "can_grade": True,
            "can_check_in": True,
            "checked_in": t.get("checked_in", False),
        }

    for t in student_trainings:
        trainings_by_id.setdefault(t["id"], t)

    trainings = list(trainings_by_id.values())

    return Response(
        CalendarPersonalSerializer(trainings, many=True).data,
        status=status.HTTP_200_OK,
    )
