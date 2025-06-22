from datetime import datetime, date, timezone
from typing import Tuple, Iterable, Optional

import pytest
from django.contrib.admin.helpers import ACTION_CHECKBOX_NAME
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APIClient

from api.crud import mark_hours
from sport.models import Training, Attendance, Semester

User = get_user_model()

before_training = datetime(2020, 1, 15, 17, 0, 0, tzinfo=timezone.utc)
training_start = datetime(2020, 1, 15, 18, 0, 0, tzinfo=timezone.utc)
training_end = datetime(2020, 1, 15, 20, 0, 0, tzinfo=timezone.utc)

change_url = reverse("admin:sport_attendance_changelist")
semester_filter_slug = "training__group__semester__id__exact={semester_id}"
period_filter_slug = "training__start__range__gte={start}&" \
                     "training__start__range__lte={end}"


def get_semester_filter(semester: Semester) -> dict:
    return {
        "training__group__semester__id__exact": semester.pk
    }
    # return semester_filter_slug.format(semester_id=semester.pk)


def get_period_filter(
        start: Optional[date] = None,
        end: Optional[date] = None
) -> str:
    return period_filter_slug.format(
        start=str(start) if start else "",
        end=str(end) if end else "",
    )


@pytest.fixture
@pytest.mark.freeze_time(before_training)
def setup(
        semester_factory,
        sport_factory,
        group_factory,
        trainer_factory,
        student_factory,
) -> Tuple[Training, User, User, Semester]:
    semester_start = date(2020, 1, 1)
    semester_end = date(2020, 2, 20)
    sem = semester_factory(
        "S1",
        semester_start,
        semester_end,
    )

    trainer_user = trainer_factory(
        email="user@foo.bar",
        password="pass"
    )

    sport = sport_factory("sport1", False)
    group = group_factory(
        "G1",
        capacity=1,
        sport=sport,
        semester=sem,
        trainer=trainer_user.trainer,
        is_club=True,
    )

    training = Training.objects.create(
        group=group,
        schedule=None,
        start=training_start,
        end=training_end,
        training_class=None,
    )

    student_user = student_factory(
        password="student",
        email="student@example.com",
    )

    return training, trainer_user, student_user, sem


def mark_attendance(
        training: Training,
        student_hours: Iterable[Tuple[User, float]],
):
    mark_hours(
        training,
        [
            (data[0].pk, data[1])
            for data in student_hours
        ]
    )


@pytest.mark.django_db
def test_empty_filters(
        setup,
        user_factory,
):
    training, trainer_user, student_user, _ = setup
    admin_password = 'password'
    admin_email = 'admin@example.com'
    user_factory(
        email=admin_email,
        password=admin_password,
        is_staff=True,
        is_superuser=True,
    )
    client = APIClient()
    client.login(
        username=admin_email,
        password=admin_password,
    )

    mark_attendance(
        training,
        [
            (student_user, 3),
        ]
    )

    qs = list(Attendance.objects.values_list(
        "id",
        flat=True,
    ))

    data = {
        'action': 'export_attendance_as_xlsx',
        ACTION_CHECKBOX_NAME: qs
    }

    response = client.post(
        change_url,
        data,
        follow=True,
    )

    content = response.content.decode().replace("\n", "")

    assert response.status_code == 200
    assert "Please filter by semester or specify training start range" in \
           content
