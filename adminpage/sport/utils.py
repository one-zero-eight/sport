from __future__ import annotations
from typing import TYPE_CHECKING

from datetime import date
from enum import IntEnum

from django.core.mail import send_mail
from django.conf import settings
from django.db.models import QuerySet
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from django.utils import timezone

if TYPE_CHECKING:
    from sport.models import Student

class SubmissionType(IntEnum):
    LINK = 1
    IMAGE = 0


def format_submission_html(
        submission_type: SubmissionType,
        submission_url: str
) -> str:
    if submission_type == SubmissionType.LINK:
        return format_html('<a href="{}">link</a>', submission_url)
    elif submission_type == SubmissionType.IMAGE:
        return format_html(
            '<a href="{}{}">image</a>',
            mark_safe(settings.BASE_URL),
            submission_url,
        )
    else:
        raise ValueError(f"Got unknown submission type: {submission_type}")


def get_study_year_from_date(in_date: date) -> int:
    new_semester_start = date.today().replace(month=8, day=20)
    delta_year = -1 if in_date < new_semester_start else 0
    return in_date.year + delta_year


def get_current_study_year() -> int:
    return get_study_year_from_date(date.today())


def set_session_notification(request, msg: str, msg_type: str):
    request.session["notify"] = (msg_type, msg)

def today() -> date:
    return timezone.now().date()


def str_or_empty(field) -> str:
    return str(field) if field else ""

def notify_students(students: QuerySet[Student], subject, message, **kwargs):
    msg = message.format(**kwargs)
    emails = list(students.values_list("user__email", flat=True).distinct())
    send_mail(
        subject,
        msg,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=emails,
        html_message=msg.replace("\n", "<br>"),
    )
