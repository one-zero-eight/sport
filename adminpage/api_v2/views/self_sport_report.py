from django.conf import settings
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiParameter
from drf_spectacular.types import OpenApiTypes
from rest_framework import status, serializers
from rest_framework.decorators import (
    parser_classes,
    permission_classes,
    api_view,
)
from rest_framework.parsers import MultiPartParser
from rest_framework.response import Response

from api_v2.crud import get_current_semester_crud, get_student_hours, get_negative_hours
from api_v2.permissions import IsStudent, IsTrainer, IsSuperUser
from api_v2.serializers import (
    SelfSportReportUploadSerializer,
    EmptySerializer,
    ErrorSerializer,
    error_detail,
    NotFoundSerializer,
)
from api_v2.serializers.self_sport_report import SelfSportTypes, ParseStrava, ParsedStravaSerializer
from sport.models import SelfSportType, SelfSportReport, Student

import requests
from bs4 import BeautifulSoup
import json
from datetime import time, datetime
import re


# =====================================================================
#                          CONSTANTS & ERRORS
# =====================================================================

class SelfSportErrors:
    NO_CURRENT_SEMESTER = (7, "You can submit self-sport only during semester")
    MEDICAL_DISALLOWANCE = (
        6, "You can't submit self-sport reports unless you pass a medical checkup"
    )
    MAX_NUMBER_SELFSPORT = (
        5, "You can't submit self-sport report, because you have max number of self sport"
    )
    INVALID_LINK = (
        4, "You can't submit link submitted previously or link is invalid."
    )


# =====================================================================
#                        SERIALIZER for results
# =====================================================================

class SelfSportReportSerializer(serializers.ModelSerializer):
    """
    Serializer for returning self-sport report results
    """
    training_type_name = serializers.CharField(source="training_type.name", read_only=True)
    student_email = serializers.EmailField(source="student.user.email", read_only=True)
    student_name = serializers.SerializerMethodField()

    class Meta:
        model = SelfSportReport
        fields = [
            "id",
            "student_email",
            "student_name",
            "training_type_name",
            "hours",
            "uploaded",
            "approval",
            "debt",
            "semester_id",
        ]

    def get_student_name(self, obj):
        s = obj.student
        return f"{s.user.first_name} {s.user.last_name}".strip() if s else None


# =====================================================================
#                         EXISTING ENDPOINTS
# =====================================================================

@extend_schema(
    methods=["GET"],
    tags=["For student"],
    summary="Get self sport types",
    description="Retrieve list of available self sport activity types that students can submit.",
    responses={status.HTTP_200_OK: SelfSportTypes(many=True)},
)
@api_view(["GET"])
def get_self_sport_types(request, **kwargs):
    sport_types = SelfSportType.objects.filter(is_active=True).all()
    serializer = SelfSportTypes(sport_types, many=True)
    return Response(serializer.data)


@extend_schema(
    methods=["POST"],
    tags=["For student"],
    summary="Upload self sport report",
    description="Submit a self sport activity report with a link to Strava, TrainingPeaks, or similar platforms. Maximum 10 hours of self sport per semester allowed.",
    request=SelfSportReportUploadSerializer,
    responses={
        status.HTTP_200_OK: EmptySerializer,
        status.HTTP_400_BAD_REQUEST: ErrorSerializer,
        status.HTTP_403_FORBIDDEN: ErrorSerializer,
    },
)
@api_view(["POST"])
@permission_classes([IsStudent])
@parser_classes([MultiPartParser])
def self_sport_upload(request, **kwargs):
    current_time = datetime.now()
    semester_start = datetime.combine(get_current_semester_crud().start, datetime.min.time())
    semester_end = datetime.combine(get_current_semester_crud().end, datetime.max.time())
    if not semester_start <= current_time <= semester_end:
        return Response(status=status.HTTP_403_FORBIDDEN, data=error_detail(*SelfSportErrors.NO_CURRENT_SEMESTER))

    serializer = SelfSportReportUploadSerializer(data=request.data)
    url = serializer.initial_data["link"]
    if SelfSportReport.objects.filter(link=url).exists() or re.match(
        r"https?://.*(?P<service>strava|tpks|trainingpeaks).*", url, re.IGNORECASE
    ) is None:
        return Response(status=status.HTTP_400_BAD_REQUEST, data=error_detail(*SelfSportErrors.INVALID_LINK))
    serializer.is_valid(raise_exception=True)
    debt = False

    student = request.user  # user.pk == user.student.pk
    if request.user.student.medical_group_id < settings.SELFSPORT_MINIMUM_MEDICAL_GROUP_ID:
        return Response(status=400, data=error_detail(*SelfSportErrors.MEDICAL_DISALLOWANCE))

    hours_info = get_student_hours(student.id)
    neg_hours = get_negative_hours(student.id, hours_info)
    if hours_info["ongoing_semester"]["hours_self_not_debt"] >= 10 and not student.has_perm(
        "sport.more_than_10_hours_of_self_sport"
    ):
        return Response(status=400, data=error_detail(*SelfSportErrors.MAX_NUMBER_SELFSPORT))

    if neg_hours < 0:
        debt = True

    serializer.save(semester=get_current_semester_crud(), student_id=student.pk, debt=debt)
    return Response({})


@extend_schema(
    methods=["GET"],
    tags=["For student"],
    summary="Parse Strava activity info",
    description="Parse activity information from a Strava link to automatically extract training data like distance, time, and calculate academic hours.",
    parameters=[ParseStrava],
    responses={
        status.HTTP_200_OK: ParsedStravaSerializer,
        status.HTTP_400_BAD_REQUEST: ErrorSerializer,
        status.HTTP_429_TOO_MANY_REQUESTS: ErrorSerializer,
    },
)
@api_view(["GET"])
@permission_classes([IsStudent])
def get_strava_activity_info(request, **kwargs):
    url = request.GET["link"]
    if re.match(r"https?://.*strava.*", url, re.IGNORECASE) is None:
        return Response(status=status.HTTP_400_BAD_REQUEST, data="Invalid link")

    resp = requests.get(url)
    if resp.status_code == 429:
        return Response(status=status.HTTP_429_TOO_MANY_REQUESTS, data="Too many requests try later")
    elif resp.status_code != 200:
        return Response(status=status.HTTP_400_BAD_REQUEST, data="Something went wrong")

    txt = resp.text
    soup = BeautifulSoup(txt)
    try:
        json_string = soup.html.body.find_all("div", attrs={"data-react-class": "ActivityPublic"})[0].get(
            "data-react-props"
        )
    except IndexError:
        return Response(status=status.HTTP_400_BAD_REQUEST, data="Invalid Strava link")

    data = json.loads(json_string)
    time_string = data["activity"]["time"]
    training_type = data["activity"]["type"]
    distance_float = float(data["activity"]["distance"][:-3])  # km

    if len(time_string) == 5:
        time_string = "00:" + time_string
    elif len(time_string) == 2:
        time_string = "00:00:" + time_string
    elif len(time_string) == 4:
        time_string = "00:0" + time_string
    elif len(time_string) == 7:
        time_string = "0" + time_string

    parsed_time = datetime.strptime(time_string, "%H:%M:%S")
    final_time = time(parsed_time.hour, parsed_time.minute + (1 if parsed_time.second else 0), 0)
    total_minutes = final_time.hour * 45 + final_time.minute
    speed = round(distance_float / (total_minutes / 60), 1)
    pace = round(total_minutes / (distance_float * 10), 1)

    approved = None
    out_dict = dict()
    out_dict["distance_km"] = distance_float
    k = 0.95  # 5% bonus for distance

    if training_type == "Run":
        academic_hours = round(distance_float / (5 * k))
        out_dict["type"] = "RUNNING"
        out_dict["speed"] = speed
        if speed >= 8.6:
            approved = True
    elif training_type == "Swim":
        distance_float += 0.05
        academic_hours = round(distance_float / (1.5 * k)) if distance_float < 3.95 else 3
        out_dict["type"] = "SWIMMING"
        out_dict["pace"] = pace
        if pace <= 2.5:
            approved = True
    elif training_type == "Ride":
        academic_hours = round(distance_float / (15 * k))
        out_dict["type"] = "BIKING"
        out_dict["speed"] = speed
        if speed >= 20:
            approved = True
    elif training_type == "Walk":
        academic_hours = round(distance_float / (6.5 * k))
        out_dict["type"] = "WALKING"
        out_dict["speed"] = speed
        if speed >= 6.5:
            approved = True

    if academic_hours > 3:
        academic_hours = 3
    out_dict["hours"] = academic_hours
    out_dict["approved"] = academic_hours > 0
    return Response(out_dict)


@api_view(["GET"])
@permission_classes([IsTrainer | IsSuperUser | IsStudent])
def get_selfsport_reports_for_student(request, student_id: int, **kwargs):
    """
    Returns all self-sport reports for the given student.
    Accessible for superusers/trainers, or the student themselves.
    """
    student = get_object_or_404(Student, pk=student_id)
    if hasattr(request.user, "student") and request.user.student.pk != student_id and not request.user.is_superuser:
        return Response({"detail": "You cannot access another student's reports."}, status=status.HTTP_403_FORBIDDEN)

    reports = (
        SelfSportReport.objects.filter(student=student)
        .select_related("training_type", "semester", "student__user")
        .order_by("-uploaded")
    )
    return Response(SelfSportReportSerializer(reports, many=True).data)


@extend_schema_view(
    get=extend_schema(
        tags=["For student"],
        summary="Get self-sport reports",
        description=(
        ),
        parameters=[
            OpenApiParameter(
                name="student_id",
                type=OpenApiTypes.INT,
                location=OpenApiParameter.QUERY,
                description=""
            ),
            OpenApiParameter(
                name="semester_id",
                type=OpenApiTypes.INT,
                location=OpenApiParameter.QUERY,
                description=""
            ),
            OpenApiParameter(
                name="approved",
                type=OpenApiTypes.BOOL,
                location=OpenApiParameter.QUERY,
                description=""
            ),
        ],
        responses={200: SelfSportReportSerializer(many=True), 404: NotFoundSerializer},
    ),
    post=extend_schema(
        operation_id="v2_selfsport_reports_create",
        tags=["For student"],
        summary="Upload self sport report",
        description="",
        request=SelfSportReportUploadSerializer,
        responses={200: EmptySerializer, 400: ErrorSerializer, 403: ErrorSerializer},
    ),
)
@api_view(["GET", "POST"])
@permission_classes([IsStudent | IsTrainer | IsSuperUser])
@parser_classes([MultiPartParser])
def self_sport_reports(request, **kwargs):
    if request.method == "GET":
        qs = SelfSportReport.objects.select_related(
            "training_type", "semester", "student__user"
        )


        is_student = hasattr(request.user, "student")
        is_elevated = bool(getattr(request.user, "is_superuser", False) or getattr(request.user, "is_staff", False))
        if is_student and not is_elevated:
            qs = qs.filter(student_id=request.user.student.pk)
        else:
            student_id = request.GET.get("student_id")
            if student_id:
                get_object_or_404(Student, pk=student_id)
                qs = qs.filter(student_id=student_id)

        semester_id = request.GET.get("semester_id")
        if semester_id:
            qs = qs.filter(semester_id=semester_id)

        approved = request.GET.get("approved")
        if approved is not None:
            val = approved.lower()
            if val in ("true", "1"):
                qs = qs.filter(approval=True)
            elif val in ("false", "0"):
                qs = qs.filter(approval=False)

        qs = qs.order_by("-uploaded")
        return Response(SelfSportReportSerializer(qs, many=True).data)

    current_time = datetime.now()
    semester_start = datetime.combine(get_current_semester_crud().start, datetime.min.time())
    semester_end = datetime.combine(get_current_semester_crud().end, datetime.max.time())
    if not semester_start <= current_time <= semester_end:
        return Response(status=status.HTTP_403_FORBIDDEN, data=error_detail(*SelfSportErrors.NO_CURRENT_SEMESTER))

    serializer = SelfSportReportUploadSerializer(data=request.data)
    url = serializer.initial_data["link"]
    if SelfSportReport.objects.filter(link=url).exists() or re.match(
        r"https?://.*(?P<service>strava|tpks|trainingpeaks).*", url, re.IGNORECASE
    ) is None:
        return Response(status=status.HTTP_400_BAD_REQUEST, data=error_detail(*SelfSportErrors.INVALID_LINK))
    serializer.is_valid(raise_exception=True)
    debt = False

    student = request.user  # user.pk == user.student.pk
    if request.user.student.medical_group_id < settings.SELFSPORT_MINIMUM_MEDICAL_GROUP_ID:
        return Response(status=400, data=error_detail(*SelfSportErrors.MEDICAL_DISALLOWANCE))

    hours_info = get_student_hours(student.id)
    neg_hours = get_negative_hours(student.id, hours_info)
    if hours_info["ongoing_semester"]["hours_self_not_debt"] >= 10 and not student.has_perm(
        "sport.more_than_10_hours_of_self_sport"
    ):
        return Response(status=400, data=error_detail(*SelfSportErrors.MAX_NUMBER_SELFSPORT))

    if neg_hours < 0:
        debt = True

    serializer.save(semester=get_current_semester_crud(), student_id=student.pk, debt=debt)
    return Response({})


@extend_schema(
    methods=["GET"],
    tags=["Self Sport"],
    summary="Get self-sport report by ID",
    description="Возвращает конкретный self-sport отчет по ID (часы, тип тренировки, статус одобрения).",
    responses={
        status.HTTP_200_OK: SelfSportReportSerializer(),
        status.HTTP_404_NOT_FOUND: NotFoundSerializer(),
        status.HTTP_403_FORBIDDEN: ErrorSerializer(),
    },
)
@api_view(["GET"])
@permission_classes([IsTrainer | IsSuperUser | IsStudent])
def get_selfsport_report_by_id(request, report_id: int, **kwargs):
    """
    Returns a single self-sport report by its ID.
    Accessible for superusers/trainers, or the student themselves.
    """
    report = get_object_or_404(
        SelfSportReport.objects.select_related("student__user", "training_type", "semester"),
        pk=report_id,
    )
    if hasattr(request.user, "student") and report.student.user.id != request.user.id and not request.user.is_superuser:
        return Response({"detail": "You cannot access another student's report."}, status=status.HTTP_403_FORBIDDEN)
    return Response(SelfSportReportSerializer(report).data)
