import pglock
from django.conf import settings
from django.db import IntegrityError
from django.shortcuts import get_object_or_404
from django.utils import timezone
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response

from api.crud.crud_training import can_check_in
from api.permissions import IsStudent, IsTrainer, IsStaff
from api.serializers import NotFoundSerializer, EmptySerializer, ErrorSerializer, error_detail
from api.serializers.training import NewTrainingInfoStudentSerializer
from api.views.attendance import AttendanceErrors
from sport.models import Training, Student, TrainingCheckIn, Attendance, Group


@extend_schema(
    methods=["GET"],
    responses={
        status.HTTP_200_OK: NewTrainingInfoStudentSerializer(),
        status.HTTP_404_NOT_FOUND: NotFoundSerializer(),
    }
)
@api_view(["GET"])
@permission_classes([IsStudent | IsTrainer | IsStaff])
def training_info(request, training_id, **kwargs):
    training = get_object_or_404(Training, pk=training_id)

    if not hasattr(request.user, 'student'):  # Allow to get training info
        return Response(NewTrainingInfoStudentSerializer({
            'training': training,
            'can_check_in': False,
            'checked_in': False,
            'hours': 0
        }).data)

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
@permission_classes([IsTrainer])
def trainer_cancel_checkin(request, training_id, student_id, **kwargs):
    try:
        training = Training.objects.get(id=training_id)
    except Training.DoesNotExist:
        return Response(
            status=status.HTTP_404_NOT_FOUND,
            data=NotFoundSerializer({'detail': 'Training not found'}).data
        )

    is_main_trainer = (training.group.trainer_id == request.user.id)
    is_in_trainers_list = training.group.trainers.filter(user_id=request.user.id).exists()

    if not (is_main_trainer or is_in_trainers_list):
        return Response(
            status=status.HTTP_403_FORBIDDEN,
            data=error_detail(2, "You are not a trainer of this group")
        )


    now = timezone.now()
    if not training.start <= now <= training.start + \
           settings.TRAINING_EDITABLE_INTERVAL:
        return Response(
            status=status.HTTP_400_BAD_REQUEST,
            data=error_detail(*AttendanceErrors.TRAINING_NOT_EDITABLE)
        )

    try:
        student = Student.objects.get(pk=student_id)
    except Student.DoesNotExist:
        return Response(
            status=status.HTTP_404_NOT_FOUND,
            data=NotFoundSerializer({'detail': 'Student not found'}).data,
        )

    try:
        TrainingCheckIn.objects.get(training_id=training_id, student=student).delete()
        return Response({})
    except TrainingCheckIn.DoesNotExist:
        return Response(
            status=status.HTTP_400_BAD_REQUEST,
            data=error_detail(1, "Student did not check in at this training")
        )
