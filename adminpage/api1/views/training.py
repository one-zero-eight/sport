import pglock
from django.db import IntegrityError
from django.shortcuts import get_object_or_404
from django.utils import timezone
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response

from api.crud.crud_training import can_check_in
from api.permissions import IsStudent
from api.serializers import NotFoundSerializer, EmptySerializer, ErrorSerializer, error_detail
from api.serializers.training import NewTrainingInfoStudentSerializer
from sport.models import Training, Student, TrainingCheckIn, Attendance


@extend_schema(
    methods=["GET"],
    responses={
        status.HTTP_200_OK: NewTrainingInfoStudentSerializer(),
        status.HTTP_404_NOT_FOUND: NotFoundSerializer(),
    }
)
@api_view(["GET"])
@permission_classes([IsStudent])
def training_info(request, training_id, **kwargs):
    training = get_object_or_404(Training, pk=training_id)
    student: Student = request.user.student
    checked_in = training.checkins.filter(student=student).exists()
    try:
        hours = Attendance.objects.get(training=training, student=student).hours
    except Attendance.DoesNotExist:
        hours = None

    return Response(NewTrainingInfoStudentSerializer({
        'training': training,
        'can_check_in': can_check_in(student, training),
        'checked_in': checked_in,
        'hours': hours
    }).data)


@extend_schema(
    methods=["POST"],
    request=None,
    responses={
        status.HTTP_200_OK: EmptySerializer(),
        status.HTTP_404_NOT_FOUND: NotFoundSerializer(),
        status.HTTP_400_BAD_REQUEST: ErrorSerializer(),
    }
)
@api_view(["POST"])
@permission_classes([IsStudent])
def training_checkin(request, training_id, **kwargs):
    try:
        training = Training.objects.get(id=training_id)
    except Training.DoesNotExist:
        return Response(
            status=status.HTTP_404_NOT_FOUND,
            data=NotFoundSerializer({'detail': 'Training not found'}).data
        )
    student: Student = request.user.student

    with pglock.advisory("check-in-lock"):  # Handle race condition
        if not can_check_in(student, training):
            return Response(
                status=status.HTTP_400_BAD_REQUEST,
                data=error_detail(2, "You cannot check in at this training")
            )

        try:
            TrainingCheckIn.objects.create(student=student, training_id=training_id)
            return Response({})
        except IntegrityError as e:
            return Response(
                status=status.HTTP_400_BAD_REQUEST,
                data=error_detail(1, "You have already checked in at this training")
            )


@extend_schema(
    methods=["POST"],
    request=None,
    responses={
        status.HTTP_200_OK: EmptySerializer(),
        status.HTTP_404_NOT_FOUND: NotFoundSerializer(),
        status.HTTP_400_BAD_REQUEST: ErrorSerializer(),
    }
)
@api_view(["POST"])
@permission_classes([IsStudent])
def training_cancel_checkin(request, training_id, **kwargs):
    try:
        training = Training.objects.get(id=training_id)
    except Training.DoesNotExist:
        return Response(
            status=status.HTTP_404_NOT_FOUND,
            data=NotFoundSerializer({'detail': 'Training not found'}).data
        )

    student: Student = request.user.student

    if training.end < timezone.now():
        return Response(
            status=status.HTTP_400_BAD_REQUEST,
            data=error_detail(2, "You cannot cancel check in at passed training")
        )

    try:
        TrainingCheckIn.objects.get(training_id=training_id, student=student).delete()
        return Response({})
    except TrainingCheckIn.DoesNotExist:
        return Response(
            status=status.HTTP_400_BAD_REQUEST,
            data=error_detail(1, "You did not check in at this training")
        )
