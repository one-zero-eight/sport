from datetime import time

from django.conf import settings
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from django.utils import timezone

from api.crud import get_sport_schedule, get_trainings_for_student, get_trainings_for_trainer
from api.permissions import IsStudent, IsTrainer
from api.serializers import CalendarRequestSerializer, CalendarSerializer


def convert_training_schedule(t) -> dict:
    return {
        "title": t["group_name"],
        "daysOfWeek": [(t["weekday"] + 1) % 7],
        "startTime": t["start"],
        "endTime": t["end"],
        "extendedProps": {
            "group_id": t["group_id"],
            "training_class": t["training_class"],
            "current_load": t["current_load"],
            "capacity": t["capacity"],
        }
    }


def convert_personal_training(t) -> dict:
    start_time = timezone.localtime(
        t["start"],
    )
    end_time = timezone.localtime(
        t["end"],
    )
    r = {
        "title": t["group_name"],
        "start": start_time,
        "end": end_time,
        "allDay": start_time.time() == time(0, 0, 0) and end_time.time() == time(23, 59, 59),
        "extendedProps": {
            "id": t["id"],
            "can_edit":
                start_time <= timezone.localtime() <= start_time +
            settings.TRAINING_EDITABLE_INTERVAL,
            "group_id": t["group_id"],
            "can_grade": t["can_grade"],
            "training_class": t["training_class"],
            "group_accredited": t["group_accredited"],
        }
    }
    if 'can_check_in' in t:
        r["extendedProps"]['can_check_in'] = t['can_check_in']
    if 'checked_in' in t:
        r["extendedProps"]['checked_in'] = t['checked_in']
    return r


@extend_schema(
    methods=["GET"],
    parameters=[CalendarRequestSerializer],
    responses={
        status.HTTP_200_OK: CalendarSerializer,
    }
)
@api_view(["GET"])
def get_schedule(request, sport_id, **kwargs):
    serializer = CalendarRequestSerializer(data=request.GET)
    serializer.is_valid(raise_exception=True)
    student = getattr(request.user, "student", None)
    trainings = get_sport_schedule(
        sport_id,
        student=student,
    )

    return Response(list(map(convert_training_schedule, trainings)))


@extend_schema(
    methods=["GET"],
    parameters=[CalendarRequestSerializer],
    responses={
        status.HTTP_200_OK: CalendarSerializer,
    }
)
@api_view(["GET"])
@permission_classes([IsStudent | IsTrainer])
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

    result_dict = dict([
        (training["id"], training)
        for training in student_trainings + trainer_trainings
    ])

    return Response(
        list(map(convert_personal_training, result_dict.values()))
    )
