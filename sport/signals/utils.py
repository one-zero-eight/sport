import datetime as dtm

from django.utils import timezone

from sport.models import Attendance, Training


def create_attendance_record(
    group,
    upload_date,
    student,
    hours,
    start=None,
    end=None,
    training_name=None,
    cause_report=None,
    cause_reference=None,
):
    tz = timezone.localtime().tzinfo
    if start is None:
        start = dtm.datetime.combine(upload_date, dtm.time(0, 0, 0), tzinfo=tz)
    if end is None:
        end = dtm.datetime.combine(upload_date, dtm.time(23, 59, 59), tzinfo=tz)
    training = Training.objects.create(
        group=group,
        start=start,
        end=end,
        custom_name=training_name,
    )
    return Attendance.objects.create(
        training=training, student=student, hours=hours, cause_report=cause_report, cause_reference=cause_reference
    )
