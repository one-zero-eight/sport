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
from api_v2.crud.crud_training import get_weekly_schedule_with_participants
from api_v2.permissions import IsStaff, IsStudent, IsTrainer
from api_v2.serializers import CalendarRequestSerializer, CalendarSerializer, CalendarPersonalSerializer, CalendarSportSerializer
from api_v2.serializers.calendar import WeeklyTrainingSerializer


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
    start_time = timezone.localtime(
        t["start"],
    )
    end_time = timezone.localtime(
        t["end"],
    )
    r = {
        "id": t["id"],
        "title": t["group_name"],
        "start": start_time,
        "end": end_time,
        "group_id": t["group_id"],
        "can_edit": start_time
            <= timezone.localtime()
            <= start_time + settings.TRAINING_EDITABLE_INTERVAL,
        "can_grade": t["can_grade"],
        "training_class": t["training_class"],
        "group_accredited": t["group_accredited"],
        "allDay": start_time.time() == time(0, 0, 0)
        and end_time.time() == time(23, 59, 59),
    }
    if "can_check_in" in t:
        r["can_check_in"] = t["can_check_in"]
    if "checked_in" in t:
        r["checked_in"] = t["checked_in"]
    return r


@extend_schema(
    methods=["GET"],
    tags=["For any user"],
    summary="Get sport schedule",
    description="Retrieve training schedule for a specific sport. Use sport_id=-1 to get all sports without specific sport type.",
    parameters=[CalendarRequestSerializer],
    responses={
        status.HTTP_200_OK: CalendarSportSerializer(many=True),
    },
)
@api_view(["GET"])
@permission_classes([IsStudent | IsStaff | IsTrainer])
def get_schedule(request, sport_id, **kwargs):
    serializer = CalendarRequestSerializer(data=request.GET)
    serializer.is_valid(raise_exception=True)
    student = getattr(request.user, "student", None)
    trainings = get_sport_schedule(
        sport_id,
        student=student,
    )
    return Response(CalendarSportSerializer(list(map(convert_training_schedule, trainings)), many=True).data)
    # return Response(list(map(convert_training_schedule, trainings)))


@extend_schema(
    methods=["GET"],
    tags=["For any user"],
    summary="Get personal schedule",
    description="Retrieve personal training schedule for the current user (student or trainer). Shows trainings relevant to the user's role.",
    parameters=[CalendarRequestSerializer],
    responses={
        status.HTTP_200_OK: CalendarPersonalSerializer(many=True),
    },
)
@api_view(["GET"])
@permission_classes([IsStudent | IsTrainer | IsStaff])
def get_personal_schedule(request, **kwargs):
    serializer = CalendarRequestSerializer(data=request.GET)
    serializer.is_valid(raise_exception=True)

    student_trainings = []
    trainer_trainings = []

    if hasattr(request.user, "student"):
        student_trainings = get_trainings_for_student(
            request.user.student,
            serializer.validated_data["start"],
            serializer.validated_data["end"],
        )

    if hasattr(request.user, "trainer"):
        trainer_trainings = get_trainings_for_trainer(
            request.user.trainer,
            serializer.validated_data["start"],
            serializer.validated_data["end"],
        )

    result_dict = dict(
        [
            (training["id"], training)
            for training in student_trainings + trainer_trainings
        ]
    )

    return Response(list(map(convert_personal_training, result_dict.values())))

