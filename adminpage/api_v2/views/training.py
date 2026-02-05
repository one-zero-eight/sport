import pglock
from django.db import IntegrityError
from django.shortcuts import get_object_or_404
from django.utils import timezone
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response

from api_v2.crud.crud_training import can_check_in
from api_v2.permissions import IsStudent, IsStaff, IsTrainer
from api_v2.serializers import (
    NotFoundSerializer,
    EmptySerializer,
    ErrorSerializer,
    error_detail,
    TrainingCheckInRequest,
)
from api_v2.serializers.training import TrainingInfoSerializer
from sport.models import Training, Student, TrainingCheckIn, Attendance


@extend_schema(
    methods=["GET"],
    tags=["For any user"],
    summary="Get training information",
    description="Retrieve detailed information about a specific training session, including whether the student can check in, is already checked in, and received hours.",
    responses={
        status.HTTP_200_OK: TrainingInfoSerializer(),
        status.HTTP_404_NOT_FOUND: NotFoundSerializer(),
    },
)
@api_view(["GET"])
@permission_classes([IsStudent | IsStaff | IsTrainer])
def training_info(request, training_id, **kwargs):
    training = get_object_or_404(Training, pk=training_id)
    # student = request.user.student
    # checked_in = training.checkins.filter(student=student).exists()
    # try:
    #     hours = Attendance.objects.get(training=training, student=student).hours
    # except Attendance.DoesNotExist:
    #     hours = None
    # data = {
    #     "training": training,
    #     "can_check_in": can_check_in(student, training),
    #     "checked_in": checked_in,
    #     "hours": hours,
    # }

    # print(data)

    return Response(TrainingInfoSerializer(training).data)


@extend_schema(
    methods=["POST"],
    tags=["For student"],
    summary="Check-in OR cancel check-in explicitly",
    description=(
        "Force action by boolean flag. "
        "`check_in=true` → perform check-in. "
        "`check_in=false` → cancel existing check-in."
    ),
    request=TrainingCheckInRequest,
    responses={
        status.HTTP_200_OK: EmptySerializer,
        status.HTTP_404_NOT_FOUND: NotFoundSerializer,
        status.HTTP_400_BAD_REQUEST: ErrorSerializer,
    },
)
@api_view(["POST"])
@permission_classes([IsStudent])
def training_checkin_view(request, training_id, **kwargs):
    req = TrainingCheckInRequest(data=request.data)
    req.is_valid(raise_exception=True)
    do_check_in: bool = req.validated_data["check_in"]

    training = get_object_or_404(Training, pk=training_id)
    student: Student = request.user.student

    already_checked_in = TrainingCheckIn.objects.filter(
        student=student, training=training
    ).exists()

    if not do_check_in:
        if not already_checked_in:
            return Response(
                status=status.HTTP_400_BAD_REQUEST,
                data=error_detail(5, "You are not checked in at this training"),
            )
        if training.end < timezone.now():
            return Response(
                status=status.HTTP_400_BAD_REQUEST,
                data=error_detail(2, "You cannot cancel check-in for a finished training"),
            )
        with pglock.advisory("check-in-lock"):
            TrainingCheckIn.objects.filter(student=student, training=training).delete()
        return Response({}, status=status.HTTP_200_OK)

    if already_checked_in:
        return Response(
            status=status.HTTP_400_BAD_REQUEST,
            data=error_detail(4, "You have already checked in at this training"),
        )

    with pglock.advisory("check-in-lock"):
        if not can_check_in(student, training):
            return Response(
                status=status.HTTP_400_BAD_REQUEST,
                data=error_detail(3, "You cannot check in at this training"),
            )
        try:
            TrainingCheckIn.objects.create(student=student, training=training)
        except IntegrityError:
            return Response(
                status=status.HTTP_400_BAD_REQUEST,
                data=error_detail(4, "You have already checked in at this training"),
            )

    return Response({}, status=status.HTTP_200_OK)