import csv
import enum
from datetime import timedelta

from django.conf import settings
from django.contrib.auth import get_user_model
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.utils import timezone
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema, OpenApiParameter, extend_schema_view
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.exceptions import PermissionDenied, NotFound
from rest_framework.response import Response
from django.views.decorators.cache import cache_page
from django.utils.dateparse import parse_date

from api_v2.crud import (
    Training,
    get_students_grades,
    mark_hours,
    get_student_last_attended_dates,
    get_student_hours,
    get_negative_hours,
    better_than,
    get_email_name_like_students_filtered_by_group,
)
from api_v2.permissions import IsStaff, IsStudent, IsTrainer, IsSuperUser
from api_v2.serializers import (
    SuggestionQuerySerializer,
    SuggestionSerializer,
    NotFoundSerializer,
    InbuiltErrorSerializer,
    TrainingGradesSerializer,
    AttendanceMarkSerializer,
    error_detail,
    BadGradeReportGradeSerializer,
    BadGradeReport,
    LastAttendedDatesSerializer,
    HoursInfoSerializer,
    HoursInfoFullSerializer,
    AttendanceSerializer,
    ErrorSerializer,
    StudentHoursSummarySerializer,
)
from api_v2.serializers.attendance import BetterThanInfoSerializer
from sport.models import Group, Student, Attendance

User = get_user_model()


class AttendanceErrors:
    TRAINING_NOT_EDITABLE = (
        2,
        f"Training not editable before it or after "
        f"{settings.TRAINING_EDITABLE_INTERVAL.days} days",
    )
    OUTBOUND_GRADES = (3, "Some students received negative marks or more than maximum")


class DateError(enum.Enum):
    OUT_OF_RANGE = 1
    INCORRECT_FORMAT = 2
    BOTH_DATES_REQUIRED = 3
    START_BEFORE_END = 4


def is_training_group(group, trainer):
    if not group.trainers.filter(pk=trainer.pk).exists():
        raise PermissionDenied(detail="You are not a teacher of this group")


def compose_bad_grade_report(email: str, hours: float) -> dict:
    return {
        "email": email,
        "hours": hours,
    }


@extend_schema(
    methods=["GET"],
    tags=["For teacher"],
    summary="Suggest students for attendance",
    description="Suggest students based on search term for attendance marking. Only accessible by trainers.",
    parameters=[SuggestionQuerySerializer],
    responses={status.HTTP_200_OK: SuggestionSerializer(many=True)},
)
@api_view(["GET"])
@permission_classes([IsStaff | IsTrainer | IsSuperUser])
def suggest_student(request, **kwargs):
    serializer = SuggestionQuerySerializer(data=request.GET)
    serializer.is_valid(raise_exception=True)

    suggested_students = get_email_name_like_students_filtered_by_group(
        serializer.validated_data["term"],
        group=serializer.validated_data["group_id"],
    )
    data = [SuggestionSerializer(
        {
            "id": student["id"],
            "first_name": student.get("first_name") or student["full_name"].split()[0],
            "last_name": (
                student["full_name"].split()[1]
                if len(student["full_name"].split()) > 1
                else ""
            ),
            "email": student["email"],
            "medical_group": student.get("medical_group__name"),
        }
    ).data 
    for student in suggested_students
    ]

    return Response(data)



@extend_schema(
    methods=["GET"],
    tags=["For teacher"],
    summary="Get training grades in CSV",
    description="'/v2/trainings/{training_id}/grades' but in CSV",
    responses={
        (status.HTTP_200_OK, "text/csv"): OpenApiTypes.BINARY,
        status.HTTP_404_NOT_FOUND: NotFoundSerializer,
        status.HTTP_403_FORBIDDEN: InbuiltErrorSerializer,
    },
)
@api_view(["GET"])
@permission_classes([IsStaff | IsTrainer | IsSuperUser])
def get_grades_csv(request, training_id, **kwargs):
    trainer = request.user  # trainer.pk == trainer.user.pk

    training = get_object_or_404(Training, pk=training_id)
    group = training.group

    if not trainer.is_superuser:
        is_training_group(group, trainer)

    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = (
        f'attachment; filename="training-{training_id}.csv"'
    )
    writer = csv.writer(response)

    writer.writerow(["Student ID", "Full Name", "Email", "Medical Group", "Hours"])
    for student in get_students_grades(training_id):
        writer.writerow(
            [
                student["student_id"],
                student["full_name"],
                student["email"],
                student["med_group"],
                student["hours"],
            ]
        )

    return response


@extend_schema_view(
    get=extend_schema(
        tags=["For teacher"],
        summary="Get training grades",
        description="Get student grades for a specific training session. Only accessible by trainers assigned to the group.",
        responses={
            status.HTTP_200_OK: TrainingGradesSerializer,
            status.HTTP_404_NOT_FOUND: NotFoundSerializer,
            status.HTTP_403_FORBIDDEN: InbuiltErrorSerializer,
        },
    ),
    post=extend_schema(
        tags=["For teacher"],
        summary="Mark student attendance",
        description=(
            "Mark attendance and assign hours for students in a training session. "
            "Only accessible by trainers assigned to the group."
        ),
        request=AttendanceMarkSerializer,
        responses={
            status.HTTP_200_OK: BadGradeReportGradeSerializer(many=True),
            status.HTTP_400_BAD_REQUEST: BadGradeReport(),
            status.HTTP_403_FORBIDDEN: InbuiltErrorSerializer,
        },
    ),
)
@api_view(["GET", "POST"])
@permission_classes([IsTrainer | IsSuperUser | IsStaff])
def training_attendance_view(request, training_id: int, **kwargs):
    trainer = request.user  # trainer.pk == trainer.user.pk

    if request.method == "GET":
        training = get_object_or_404(Training, pk=training_id)
        group = training.group

        if not trainer.is_superuser:
            is_training_group(group, trainer)

        return Response({"students": get_students_grades(training_id)})

    serializer = AttendanceMarkSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    try:
        training = (
            Training.objects.select_related("group")
            .only("group__trainer", "start", "end")
            .get(pk=training_id)
        )
    except Training.DoesNotExist:
        raise NotFound()

    if not trainer.is_superuser:
        is_training_group(training.group, trainer)

    now = timezone.now()
    if not (
        training.start <= now <= training.start + settings.TRAINING_EDITABLE_INTERVAL
    ):
        return Response(
            status=status.HTTP_400_BAD_REQUEST,
            data=error_detail(*AttendanceErrors.TRAINING_NOT_EDITABLE),
        )

    id_to_hours = {
        item["student_id"]: item["hours"]
        for item in serializer.validated_data["students_hours"]
    }

    max_hours = training.academic_duration
    students = User.objects.filter(pk__in=id_to_hours.keys()).only("email")

    hours_to_mark = []
    negative_mark = []
    overflow_mark = []

    for student in students:
        hours_put = id_to_hours[student.pk]
        if hours_put < 0:
            negative_mark.append(compose_bad_grade_report(student.email, hours_put))
        elif hours_put > max_hours:
            overflow_mark.append(compose_bad_grade_report(student.email, hours_put))
        elif (
            str(
                Student.objects.filter(
                    user=get_user_model().objects.filter(email=student.email)[0]
                )[0].student_status
            )
            != "Normal"
        ):
            continue
        else:
            hours_to_mark.append((student, hours_put))

    if negative_mark or overflow_mark:
        return Response(
            status=status.HTTP_400_BAD_REQUEST,
            data={
                **error_detail(*AttendanceErrors.OUTBOUND_GRADES),
                "negative_marks": negative_mark,
                "overflow_marks": overflow_mark,
            },
        )

    # Apply attendance updates
    mark_data = [(x[0].pk, x[1]) for x in hours_to_mark]
    mark_hours(training, mark_data)

    return Response([compose_bad_grade_report(x[0].email, x[1]) for x in hours_to_mark])


@extend_schema(
    methods=["GET"],
    tags=["For student"],
    summary="Get student hours summary",
    description="Get comprehensive student hours summary including debt, self-sport hours, hours from groups, and required hours. Use 'current_semester_only' parameter to get data for current semester only or all semesters.",
    responses={
        status.HTTP_200_OK: StudentHoursSummarySerializer,
        status.HTTP_404_NOT_FOUND: NotFoundSerializer,
        status.HTTP_403_FORBIDDEN: InbuiltErrorSerializer,
    },
)
@api_view(["GET"])
@permission_classes([IsStudent])
def get_student_hours_summary(request, student_id, **kwargs):
    try:
        from api_v2.crud.crud_attendance import get_student_hours_summary

        summary = get_student_hours_summary(student_id)
        #summary.update({"better_than": get_better_than_info(student_id)})
        return Response(summary)
    except Student.DoesNotExist:
        return Response(
            {"detail": "Student not found"}, status=status.HTTP_404_NOT_FOUND
        )


@extend_schema(
    methods=["GET"],
    tags=["For student"],
    summary="Get student performance ranking",
    description="Get student's performance ranking compared to other students (percentage of students performing worse).",
    responses={
        status.HTTP_200_OK: BetterThanInfoSerializer,
        status.HTTP_404_NOT_FOUND: NotFoundSerializer,
        status.HTTP_403_FORBIDDEN: InbuiltErrorSerializer,
    },
)
@api_view(["GET"])
@permission_classes([IsStudent | IsStaff | IsSuperUser])
@cache_page(60 * 60 * 24)
def get_better_than_info(request, student_id: int, **kwargs):
    value = better_than(student_id)         # float в [0,1]
    return Response({"better_than": value})

