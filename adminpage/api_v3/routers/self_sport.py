import datetime
import json
import re
from typing import Any

import requests
from bs4 import BeautifulSoup
from django.conf import settings
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, AnyUrl, Field, AliasPath, field_validator
from starlette import status

from api_v3.dependencies import VerifiedDep
from api_v3.utils.semester import get_current_semester
from api_v3.permissions import is_student, is_admin
from sport.models import SelfSportType, SelfSportReport, Student, Semester, Attendance, Debt

router = APIRouter(
    tags=["Self sport"],
    responses={
        401: {"description": "Invalid token"},
        403: {"description": "Unauthorized"},
    },
)


class SelfSportTypeSchema(BaseModel):
    id: int
    name: str
    application_rule: str | None = None


class SelfSportReportCreateSchema(BaseModel):
    link: AnyUrl
    training_type: int
    hours: int
    student_comment: str | None = None
    parsed_data: dict[str, Any] | None = None


class SelfSportReportSchema(BaseModel):
    id: int
    student_email: str = Field(
        validation_alias=AliasPath("student", "user", "email")
    )
    student_name: str | None = Field(validation_alias="student")
    training_type_name: str | None = Field(default=None, validation_alias=AliasPath("training_type", "name"))
    hours: int
    uploaded: datetime.datetime
    approval: bool | None
    debt: bool
    semester_id: int

    @field_validator("student_name", mode="before")
    @classmethod
    def build_student_name(cls, v: Any) -> str | None:
        if v is None:
            return None
        student = v
        user = getattr(student, "user", None)
        if user is None:
            return None
        first = getattr(user, "first_name", "") or ""
        last = getattr(user, "last_name", "") or ""
        full = f"{first} {last}".strip()
        return full or None


class ParsedStravaSchema(BaseModel):
    distance_km: float
    type: str | None = None
    pace: float | None = None
    speed: float | None = None
    hours: int
    approved: bool


class SelfSportErrors:
    NO_CURRENT_SEMESTER = (7, "You can submit self-sport only during semester")
    MEDICAL_DISALLOWANCE = (
        6,
        "You can't submit self-sport reports unless you pass a medical checkup",
    )
    MAX_NUMBER_SELFSPORT = (
        5,
        "You can't submit self-sport report, because you have max number of self sport",
    )
    INVALID_LINK = (
        4,
        "You can't submit link submitted previously or link is invalid.",
    )


@router.get(
    "/self-sport/types",
    responses={
        200: {"description": "Get self sport types"},
    },
)
def get_self_sport_types(_user: VerifiedDep) -> list[SelfSportTypeSchema]:
    """
    Retrieve list of available self sport activity types.
    """
    sport_types = SelfSportType.objects.filter(is_active=True).all()
    return [
        SelfSportTypeSchema.model_validate(t, from_attributes=True)
        for t in sport_types
    ]


@router.get(
    "/self-sport/parse-strava",
    responses={
        200: {"description": "Parse Strava activity info"},
        400: {"description": "Invalid link or request"},
        429: {"description": "Too many requests"},
    },
)
def parse_self_sport_strava(
    user: VerifiedDep,
    link: AnyUrl = Query(..., description="Strava activity link"),
) -> ParsedStravaSchema:
    """
    Parse Strava activity information and calculate academic hours.
    """
    if not is_student(user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only students can parse Strava activities",
        )

    if re.match(r"https?://.*strava.*", str(link), re.IGNORECASE) is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid link",
        )

    resp = requests.get(str(link))
    if resp.status_code == 429:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many requests try later",
        )
    if resp.status_code != 200:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Something went wrong",
        )

    txt = resp.text
    soup = BeautifulSoup(txt, "html.parser")
    try:
        json_string = soup.html.body.find_all(
            "div", attrs={"data-react-class": "ActivityPublic"}
        )[0].get("data-react-props")
    except IndexError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid Strava link",
        )

    data = json.loads(json_string)
    time_string = data["activity"]["time"]
    training_type = data["activity"]["type"]
    distance_float = float(data["activity"]["distance"][:-3])

    if len(time_string) == 5:
        time_string = "00:" + time_string
    elif len(time_string) == 2:
        time_string = "00:00:" + time_string
    elif len(time_string) == 4:
        time_string = "00:0" + time_string
    elif len(time_string) == 7:
        time_string = "0" + time_string

    parsed_time = datetime.datetime.strptime(time_string, "%H:%M:%S")
    final_time = datetime.time(
        parsed_time.hour,
        parsed_time.minute + (1 if parsed_time.second else 0),
        0,
    )
    total_minutes = final_time.hour * 45 + final_time.minute
    speed = round(distance_float / (total_minutes / 60), 1)
    pace = round(total_minutes / (distance_float * 10), 1)

    distance_km = distance_float  # Used for the response (even if we mutate `distance_float` below).
    training_type_name: str | None = None
    speed_out: float | None = None
    pace_out: float | None = None
    k = 0.95

    if training_type == "Run":
        academic_hours = round(distance_float / (5 * k))
        training_type_name = "RUNNING"
        speed_out = speed
    elif training_type == "Swim":
        distance_float += 0.05
        academic_hours = (
            round(distance_float / (1.5 * k)) if distance_float < 3.95 else 3
        )
        training_type_name = "SWIMMING"
        pace_out = pace
    elif training_type == "Ride":
        academic_hours = round(distance_float / (15 * k))
        training_type_name = "BIKING"
        speed_out = speed
    elif training_type == "Walk":
        academic_hours = round(distance_float / (6.5 * k))
        training_type_name = "WALKING"
        speed_out = speed
    else:
        academic_hours = 0

    if academic_hours > 3:
        academic_hours = 3

    return ParsedStravaSchema(
        distance_km=distance_km,
        type=training_type_name,
        pace=pace_out,
        speed=speed_out,
        hours=academic_hours,
        approved=academic_hours > 0,
    )


@router.get(
    "/self-sport/reports",
    responses={
        200: {"description": "Get self-sport reports"},
    },
)
def list_self_sport_reports(
    user: VerifiedDep,
    student_id: int | None = Query(
        None,
        description="Filter by student ID (trainers/admins only, students can only see their own)",
    ),
    semester_id: int | None = Query(
        None,
        description="Filter by semester ID; if omitted, all semesters are returned",
    ),
) -> list[SelfSportReportSchema]:
    """
    Returns self-sport reports with access rules similar to v2.
    """
    qs = SelfSportReport.objects.select_related(
        "training_type", "semester", "student__user"
    )

    if is_student(user) and not is_admin(user):
        if student_id and student_id != user.student_or_none.pk:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You cannot access another student's reports.",
            )
        qs = qs.filter(student_id=user.student_or_none.pk)
    else:
        if student_id:
            if not Student.objects.filter(pk=student_id).exists():
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Student not found",
                )
            qs = qs.filter(student_id=student_id)

    if semester_id:
        qs = qs.filter(semester_id=semester_id)

    qs = qs.order_by("-uploaded")
    return [
        SelfSportReportSchema.model_validate(r, from_attributes=True) for r in qs
    ]


@router.post(
    "/self-sport/reports",
    responses={
        200: {"description": "Upload self sport report"},
        400: {"description": "Invalid request"},
    },
)
def create_self_sport_report(
    user: VerifiedDep,
    body: SelfSportReportCreateSchema,
) -> None:
    """
    Create a new self-sport report with the same business rules as v2.
    """
    if not is_student(user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only students can submit self-sport reports",
        )

    current_time = datetime.datetime.now()
    semester = get_current_semester()
    semester_start = datetime.datetime.combine(semester.start, datetime.datetime.min.time())
    semester_end = datetime.datetime.combine(semester.end, datetime.datetime.max.time())
    if not (semester_start <= current_time <= semester_end):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=SelfSportErrors.NO_CURRENT_SEMESTER[1],
        )

    url = str(body.link)
    if SelfSportReport.objects.filter(link=url).exists() or re.match(
        r"https?://.*(?P<service>strava|tpks|trainingpeaks).*", url, re.IGNORECASE
    ) is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=SelfSportErrors.INVALID_LINK[1],
        )

    if user.student_or_none.medical_group_id < settings.SELFSPORT_MINIMUM_MEDICAL_GROUP_ID:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=SelfSportErrors.MEDICAL_DISALLOWANCE[1],
        )

    student_id = user.id
    student = Student.objects.get(user_id=student_id)
    current_semester = get_current_semester()

    sem_info_cur = {
        "id_sem": current_semester.id,
        "hours_not_self": 0.0,
        "hours_self_not_debt": 0.0,
        "hours_self_debt": 0.0,
        "hours_sem_max": float(current_semester.hours),
        "debt": 0.0,
    }
    try:
        sem_info_cur["debt"] = Debt.objects.get(
            semester_id=current_semester.id, student_id=student_id
        ).debt
    except Debt.DoesNotExist:
        pass

    query_attend = Attendance.objects.filter(
        student_id=student_id,
        training__group__semester=current_semester,
    )
    for sem in query_attend:
        if sem.cause_report is None:
            sem_info_cur["hours_not_self"] += float(sem.hours)
        elif sem.cause_report.debt is True:
            sem_info_cur["hours_self_debt"] += float(sem.hours)
        else:
            sem_info_cur["hours_self_not_debt"] += float(sem.hours)

    last_semesters = Semester.objects.filter(
        end__lt=current_semester.start
    ).order_by("-end")
    last_sem_info_arr = []
    sem_info = {
        "id_sem": 0,
        "hours_not_self": 0.0,
        "hours_self_not_debt": 0.0,
        "hours_self_debt": 0.0,
        "hours_sem_max": 0.0,
        "debt": 0.0,
    }

    for sem in last_semesters:
        if student in sem.academic_leave_students.all():
            continue
        if sem.end.year >= student.enrollment_year:
            sem_info["id_sem"] = sem.id
            sem_info["hours_sem_max"] = sem.hours
            try:
                # Note: preserved original query behavior (uses `current_semester.id`).
                sem_info["debt"] = Debt.objects.get(
                    semester_id=current_semester.id, student_id=student_id
                ).debt
            except Debt.DoesNotExist:
                pass
            for att in Attendance.objects.filter(
                student_id=student_id, training__group__semester=sem
            ):
                if att.cause_report is None:
                    sem_info["hours_not_self"] += float(att.hours)
                elif att.cause_report.debt is True:
                    sem_info["hours_self_debt"] += float(att.hours)
                else:
                    sem_info["hours_self_not_debt"] += float(att.hours)
            last_sem_info_arr.append(sem_info.copy())

        sem_info = {
            "id_sem": 0,
            "hours_not_self": 0.0,
            "hours_self_not_debt": 0.0,
            "hours_self_debt": 0.0,
            "hours_sem_max": 0.0,
            "debt": 0.0,
        }

    hours_info = {"last_semesters_hours": last_sem_info_arr, "ongoing_semester": sem_info_cur}

    sem_now = hours_info["ongoing_semester"]
    current_semester = get_current_semester()
    try:
        debt = Debt.objects.get(student=student_id, semester=current_semester).debt
    except Debt.DoesNotExist:
        debt = 0
    neg_hours = (
        sem_now["hours_self_debt"]
        + sem_now["hours_not_self"]
        + sem_now["hours_self_not_debt"]
        - debt
    )
    if hours_info["ongoing_semester"]["hours_self_not_debt"] >= 10 and not user.has_perm(
        "sport.more_than_10_hours_of_self_sport"
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=SelfSportErrors.MAX_NUMBER_SELFSPORT[1],
        )

    debt = neg_hours < 0

    try:
        training_type = SelfSportType.objects.get(
            pk=body.training_type, is_active=True
        )
    except SelfSportType.DoesNotExist:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Self sport type not found",
        )

    SelfSportReport.objects.create(
        link=url,
        hours=body.hours,
        training_type=training_type,
        student_comment=body.student_comment or "",
        parsed_data=body.parsed_data or {},
        semester=semester,
        student_id=user.id,
        debt=debt,
    )
    return None


@router.get(
    "/self-sport/reports/{report_id}",
    responses={
        200: {"description": "Get self-sport report by ID"},
        404: {"description": "Not found"},
    },
)
def get_self_sport_report_by_id(
    user: VerifiedDep,
    report_id: int,
) -> SelfSportReportSchema:
    """
    Get a self-sport report by ID with access control.
    """
    try:
        report = SelfSportReport.objects.select_related(
            "student__user",
            "training_type",
            "semester",
        ).get(pk=report_id)
    except SelfSportReport.DoesNotExist:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Self sport report not found",
        )

    if is_student(user) and not is_admin(user):
        if report.student.user_id != user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You cannot access another student's report.",
            )

    return SelfSportReportSchema.model_validate(report, from_attributes=True)

