from django.conf import settings
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.decorators import (
    parser_classes,
    permission_classes,
    api_view,
)
from rest_framework.parsers import MultiPartParser
from rest_framework.response import Response

from api.crud import get_ongoing_semester, get_student_hours, get_negative_hours
from api.permissions import IsStudent
from api.serializers import (
    SelfSportReportUploadSerializer,
    EmptySerializer,
    ErrorSerializer,
    error_detail,
)
from api.serializers.self_sport_report import SelfSportTypes, ParseStrava, ParsedStravaSerializer
from sport.models import SelfSportType, SelfSportReport
import requests
from bs4 import BeautifulSoup, SoupStrainer
import json
from datetime import time, datetime
import re


class SelfSportErrors:
    NO_CURRENT_SEMESTER = (
        7, "You can submit self-sport only during semester"
    )
    MEDICAL_DISALLOWANCE = (
        6, "You can't submit self-sport reports "
           "unless you pass a medical checkup"
    )
    MAX_NUMBER_SELFSPORT = (
        5, "You can't submit self-sport report, because you have max number of self sport"
    )
    INVALID_LINK = (
        4, "You can't submit link submitted previously or link is invalid."
    )


@extend_schema(
    methods=["Get"],
    responses={
        status.HTTP_200_OK: SelfSportTypes(many=True),
    }
)
@api_view(["GET"])
def get_self_sport_types(request, **kwargs):
    sport_types = SelfSportType.objects.filter(
        is_active=True
    ).all()
    serializer = SelfSportTypes(sport_types, many=True)
    return Response(serializer.data)


@extend_schema(
    methods=["POST"],
    description="One link to Strava required (begins with http(s)://)",
    request=SelfSportReportUploadSerializer,
    responses={
        status.HTTP_200_OK: EmptySerializer,
        status.HTTP_400_BAD_REQUEST: ErrorSerializer,
        status.HTTP_403_FORBIDDEN: ErrorSerializer
    }
)
@api_view(["POST"])
@permission_classes([IsStudent])
@parser_classes([MultiPartParser])
def self_sport_upload(request, **kwargs):
    current_time = datetime.now()
    semester_start = datetime.combine(
        get_ongoing_semester().start, datetime.min.time())
    semester_end = datetime.combine(
        get_ongoing_semester().end, datetime.max.time())
    if not semester_start <= current_time <= semester_end:
        return Response(
            status=status.HTTP_403_FORBIDDEN,
            data=error_detail(*SelfSportErrors.NO_CURRENT_SEMESTER)
        )

    serializer = SelfSportReportUploadSerializer(data=request.data)
    url = serializer.initial_data['link']
    if SelfSportReport.objects.filter(link=url).exists() or re.match(
        r'https?://.*(?P<service>strava|tpks|trainingpeaks).*', url, re.IGNORECASE) is None:
        return Response(
            status=status.HTTP_400_BAD_REQUEST,
            data=error_detail(*SelfSportErrors.INVALID_LINK)
        )
    serializer.is_valid(raise_exception=True)
    debt = False

    student = request.user  # user.pk == user.student.pk
    if request.user.student.medical_group_id \
        < settings.SELFSPORT_MINIMUM_MEDICAL_GROUP_ID:
        return Response(
            status=400,
            data=error_detail(*SelfSportErrors.MEDICAL_DISALLOWANCE),
        )
    hours_info = get_student_hours(student.id)
    neg_hours = get_negative_hours(student.id, hours_info)
    if hours_info['ongoing_semester']['hours_self_not_debt'] >= 10 \
        and not student.has_perm('sport.more_than_10_hours_of_self_sport'):
        return Response(
            status=400,
            data=error_detail(*SelfSportErrors.MAX_NUMBER_SELFSPORT),
        )

    if neg_hours < 0:
        debt = True

    # image = None

    # if 'image' in serializer.validated_data:
    #     image, error = process_image(serializer.validated_data['image'])
    #     if error is not None:
    #         return error

    serializer.save(
        # image=image,
        semester=get_ongoing_semester(),
        student_id=student.pk,
        debt=debt
    )

    return Response({})


@extend_schema(
    methods=["GET"],
    description="Strava link parsing",
    parameters=[ParseStrava],
    responses={
        status.HTTP_200_OK: ParsedStravaSerializer,
        status.HTTP_400_BAD_REQUEST: ErrorSerializer,
        status.HTTP_429_TOO_MANY_REQUESTS: ErrorSerializer,
    }
)
@api_view(["GET"])
@permission_classes([IsStudent])
def get_strava_activity_info(request, **kwargs):
    url = request.GET['link']
    if re.match(r'https?://.*strava.*', url, re.IGNORECASE) is None:
        return Response(
            status=status.HTTP_400_BAD_REQUEST,
            data="Invalid link"
        )
    resp = requests.get(url)
    if resp.status_code == 429:
        return Response(
            status=status.HTTP_429_TOO_MANY_REQUESTS,
            data="Too many requests try later"
        )
    elif resp.status_code != 200:
        return Response(
            status=status.HTTP_400_BAD_REQUEST,
            data="Something went wrong"
        )
    txt = requests.get(url).text
    soup = BeautifulSoup(txt)
    try:
        json_string = soup.html.body.find_all(
            'div', attrs={"data-react-class": "ActivityPublic"})[0].get("data-react-props")
    except IndexError:
        return Response(
            status=status.HTTP_400_BAD_REQUEST,
            data="Invalid Strava link"
        )
    data = json.loads(json_string)
    beautified_data = json.dumps(data, sort_keys=True, indent=2)

    time_string = data['activity']["time"]
    training_type = data['activity']["type"]
    distance_float = float(data['activity']["distance"][:-3])  # km

    if (len(time_string) == 5):
        time_string = "00:" + time_string
    elif (len(time_string) == 2):
        time_string = "00:00:" + time_string
    elif (len(time_string) == 4):
        time_string = "00:0" + time_string
    elif (len(time_string) == 7):
        time_string = "0" + time_string
    format_string = "%H:%M:%S"

    parsed_time = datetime.strptime(time_string, format_string)
    if parsed_time.second != 0:
        if parsed_time.minute == 59:
            final_time = time(parsed_time.hour + 1, 0, 0)
        else:
            final_time = time(parsed_time.hour, parsed_time.minute + 1, 0)
    total_minutes = final_time.hour * 45 + final_time.minute

    speed = round(distance_float / (total_minutes / 60), 1)  # for Run, Ride, Walk
    pace = round(total_minutes / (distance_float * 10), 1)  # for Swim

    approved = None
    out_dict = dict()
    out_dict['distance_km'] = distance_float
    k = 0.95  # 5% bonus for distanse
    if training_type == "Run":
        academic_hours = round(distance_float / (5 * k))
        out_dict['type'] = 'RUNNING'
        out_dict['speed'] = speed
        if speed >= 8.6:
            approved = True
    elif training_type == "Swim":
        distance_float += 0.05  # bonus 50m because Strava unauth rounds by 1 digit
        if distance_float < 3.95:
            academic_hours = round(distance_float / (1.5 * k))
        else:
            academic_hours = 3
        out_dict['type'] = 'SWIMMING'
        out_dict['pace'] = pace
        if pace <= 2.5:
            approved = True
    elif training_type == "Ride":
        academic_hours = round(distance_float / (15 * k))
        out_dict['type'] = 'BIKING'
        out_dict['speed'] = speed
        if speed >= 20:
            approved = True
    elif training_type == "Walk":
        academic_hours = round(distance_float / (6.5 * k))
        out_dict['type'] = 'WALKING'
        out_dict['speed'] = speed
        if speed >= 6.5:
            approved = True
    if academic_hours > 3:
        academic_hours = 3
    out_dict['hours'] = academic_hours
    if academic_hours <= 0:
        approved = False
    else:
        approved = True

    out_dict['approved'] = approved

    return Response(out_dict)
