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
)
from api_v2.serializers.training import NewTrainingInfoStudentSerializer
from sport.models import Training, Student, TrainingCheckIn, Attendance


@extend_schema(
    methods=["GET"],
    tags=["For teacher"],
    summary="Get training information",
    description="Retrieve detailed information about a specific training session, including whether the student can check in, is already checked in, and received hours.",
    responses={
        status.HTTP_200_OK: NewTrainingInfoStudentSerializer(),
        status.HTTP_404_NOT_FOUND: NotFoundSerializer(),
    },
)
@api_view(["GET"])
@permission_classes([IsStaff | IsTrainer])
def training_info(request, training_id, **kwargs):
    training = get_object_or_404(Training, pk=training_id)
    student: Student = request.user.student
    checked_in = training.checkins.filter(student=student).exists()
    try:
        hours = Attendance.objects.get(training=training, student=student).hours
    except Attendance.DoesNotExist:
        hours = None

    return Response(
        NewTrainingInfoStudentSerializer(
            {
                "training": training,
                "can_check_in": can_check_in(student, training),
                "checked_in": checked_in,
                "hours": hours,
            }
        ).data
    )


@extend_schema(
    methods=["POST"],
    tags=["For student"],
    summary="Check-in or cancel check-in for training",
    description=(
        "Checks if the student can check in or cancel the check-in for a training. "
        "Automatically determines whether to check in or cancel depending on current state."
    ),
    request=None,
    responses={
        status.HTTP_200_OK: EmptySerializer(),
        status.HTTP_404_NOT_FOUND: NotFoundSerializer(),
        status.HTTP_400_BAD_REQUEST: ErrorSerializer(),
    },
)
@api_view(["POST"])
@permission_classes([IsStudent])
def training_checkin_view(request, training_id, **kwargs):
    """
    Unified endpoint for check-in and cancel check-in.
    Behavior:
    - If the student is not checked in → performs check-in (same as /check-in)
    - If already checked in → cancels check-in (same as /cancel-check-in)
    """

    training = get_object_or_404(Training, pk=training_id)
    student: Student = request.user.student

    # Determine if already checked in
    already_checked_in = TrainingCheckIn.objects.filter(
        student=student, training=training
    ).exists()

    # === Case 1: Cancel check-in if already checked in ===
    if already_checked_in:
        if training.end < timezone.now():
            return Response(
                status=status.HTTP_400_BAD_REQUEST,
                data=error_detail(2, "You cannot cancel check-in for a finished training"),
            )

        TrainingCheckIn.objects.filter(student=student, training=training).delete()
        return Response(
            {},
            status=status.HTTP_200_OK,
        )

    # === Case 2: Perform check-in ===
    with pglock.advisory("check-in-lock"):
        if not can_check_in(student, training):
            return Response(
                status=status.HTTP_400_BAD_REQUEST,
                data=error_detail(3, "You cannot check in at this training"),
            )

        try:
            TrainingCheckIn.objects.create(student=student, training=training)
            return Response({}, status=status.HTTP_200_OK)
        except IntegrityError:
            return Response(
                status=status.HTTP_400_BAD_REQUEST,
                data=error_detail(4, "You have already checked in at this training"),
            )
