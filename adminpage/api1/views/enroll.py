from django.db import transaction, InternalError, IntegrityError
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response

from api.crud import (
    unenroll_student,
    enroll_student, get_ongoing_semester,
)
from api.permissions import IsStudent, IsTrainer, SportSelected
from api.serializers import (
    EnrollSerializer,
    error_detail,
    EmptySerializer,
    NotFoundSerializer,
    ErrorSerializer, UnenrollStudentSerializer,
)
from api.views.attendance import is_training_group
from sport.models import Group, Student, Enroll


class EnrollErrors:
    GROUP_IS_FULL = (2, "Group you chosen is full")
    TOO_MUCH_GROUPS = (3, "You have enrolled to too much groups")
    DOUBLE_ENROLL = (4, "You can't enroll to a group "
                        "you have already enrolled to"
                     )
    INCONSISTENT_UNENROLL = (5, "You are not enrolled to the group")
    MEDICAL_DISALLOWANCE = (6, "You can't enroll to the group "
                               "due to your medical group")
    NOT_ENROLLED = (7, "Requested student is not enrolled into this group")
    SPORT_ERROR = (8, "Requested group doesn't belong to requested student's sport")
    SEMESTER_ERROR = (9, "Requested group does't belong to current semester")
    QR_ERROR = (10, "Requested group has QR requirement")


@extend_schema(
    methods=["POST"],
    request=EnrollSerializer,
    responses={
        status.HTTP_200_OK: EmptySerializer,
        status.HTTP_404_NOT_FOUND: NotFoundSerializer,
        status.HTTP_400_BAD_REQUEST: ErrorSerializer,
    },
)
@api_view(["POST"])
@permission_classes([IsStudent, SportSelected])
@transaction.atomic
def enroll(request, **kwargs):
    """
    Enroll student

    error codes:
    2 - Group you chosen is full
    3 - You have too much secondary groups
    4 - You can't enroll to a group you have already enrolled to
    6 - Enroll with insufficient medical group
    """
    serializer = EnrollSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    group = get_object_or_404(
        Group,
        pk=serializer.validated_data["group_id"]
    )
    student = request.user.student
    if student.sport != group.sport:
        return Response(
            status=status.HTTP_400_BAD_REQUEST,
            data=error_detail(*EnrollErrors.SPORT_ERROR)
        )
    if Enroll.objects.filter(group=group, student=student).exists():
        return Response(
            status=status.HTTP_400_BAD_REQUEST,
            data=error_detail(
                *EnrollErrors.DOUBLE_ENROLL
            )
        )
    if Group.objects.filter(semester=get_ongoing_semester(), enrolls__student=student).exists():
        return Response(
            status=status.HTTP_400_BAD_REQUEST,
            data=error_detail(*EnrollErrors.TOO_MUCH_GROUPS)
        )
    if group.semester.id is not get_ongoing_semester().id:
        return Response(
            status=status.HTTP_400_BAD_REQUEST,
            data=error_detail(*EnrollErrors.SEMESTER_ERROR)
        )

    if not group.allowed_medical_groups.filter(id=student.medical_group.id).exists():
        return Response(
            status=status.HTTP_400_BAD_REQUEST,
            data=error_detail(*EnrollErrors.MEDICAL_DISALLOWANCE)
        )

    # if group.allowed_qr not in [-1, int(student.has_QR)]:
    #     return Response(
    #         status=status.HTTP_400_BAD_REQUEST,
    #         data=error_detail(*EnrollErrors.QR_ERROR)
    #     )

    try:
        enroll_student(group, student)
    except IntegrityError:
        return Response(
            status=status.HTTP_400_BAD_REQUEST,
            data=error_detail(
                *EnrollErrors.DOUBLE_ENROLL
            )
        )
    except InternalError as e:
        if "too much groups" in str(e):
            return Response(
                status=status.HTTP_400_BAD_REQUEST,
                data=error_detail(
                    *EnrollErrors.TOO_MUCH_GROUPS
                )
            )
        else:
            return Response(
                status=status.HTTP_400_BAD_REQUEST,
                data=error_detail(
                    *EnrollErrors.GROUP_IS_FULL
                )
            )
    return Response({})


@extend_schema(
    methods=["POST"],
    request=EnrollSerializer,
    responses={
        status.HTTP_200_OK: EmptySerializer,
        status.HTTP_404_NOT_FOUND: NotFoundSerializer,
        status.HTTP_400_BAD_REQUEST: ErrorSerializer,
    },
)
@api_view(["POST"])
@permission_classes([IsStudent])
@transaction.atomic
def unenroll(request, **kwargs):
    """
    Unenroll student

    Error codes:
    5 - Can't unenroll from primary group
    """
    serializer = EnrollSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    group = get_object_or_404(
        Group,
        pk=serializer.validated_data["group_id"]
    )
    student = request.user.student
    removed_count = unenroll_student(group, student)
    if removed_count == 0:
        return Response(
            status=status.HTTP_400_BAD_REQUEST,
            data=error_detail(
                *EnrollErrors.INCONSISTENT_UNENROLL
            )
        )
    return Response({})


@extend_schema(
    methods=["POST"],
    request=UnenrollStudentSerializer,
    responses={
        status.HTTP_200_OK: EmptySerializer,
        status.HTTP_404_NOT_FOUND: NotFoundSerializer,
        status.HTTP_400_BAD_REQUEST: ErrorSerializer,
    },
)
@api_view(["POST"])
@permission_classes([IsTrainer])
@transaction.atomic
def unenroll_by_trainer(request, **kwargs):
    """
    Unenroll student

    Error codes:
    5 - Can't unenroll from primary group
    """
    serializer = UnenrollStudentSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    group = get_object_or_404(
        Group,
        pk=serializer.validated_data["group_id"]
    )

    is_training_group(group, request.user)

    student = get_object_or_404(
        Student,
        pk=serializer.validated_data["student_id"]
    )

    removed_count = unenroll_student(group, student)
    if removed_count == 0:
        return Response(
            status=status.HTTP_400_BAD_REQUEST,
            data=error_detail(
                *EnrollErrors.NOT_ENROLLED
            )
        )
    return Response({})
