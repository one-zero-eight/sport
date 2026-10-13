import datetime as dtm
import tempfile

import pytest
from django.conf import settings
from django.utils import timezone
from PIL import Image
from rest_framework import status
from rest_framework.test import APIClient

from api_v1.views.reference import ReferenceErrors
from sport.models import Attendance, Reference, Training


@pytest.mark.django_db
@pytest.mark.freeze_time(dtm.date(2020, 1, 2))
def test_reference_upload(student_factory, semester_factory, freezer):
    email = "user@foo.bar"
    password = "pass"
    user = student_factory(
        email=email,
        password=password,
    )
    semester = semester_factory(
        name="S20",
        start=dtm.date(2020, 1, 1),
        end=dtm.date(2020, 1, 15),
    )
    client = APIClient()
    client.login(
        email=email,
        password=password,
    )
    image_sm = Image.new("RGB", (600, 300))
    image_md = Image.new("RGB", (600, 600))
    image_lg = Image.new("RGB", (600, 5500))
    # Kept open for multiple multipart posts; closed when the test ends.
    file_sm = tempfile.NamedTemporaryFile(suffix=".jpg")  # noqa: SIM115
    file_md = tempfile.NamedTemporaryFile(suffix=".jpg")  # noqa: SIM115
    file_lg = tempfile.NamedTemporaryFile(suffix=".jpg")  # noqa: SIM115
    image_sm.save(file_sm)
    image_md.save(file_md)
    image_lg.save(file_lg)
    file_sm.seek(0)
    file_md.seek(0)
    file_lg.seek(0)
    response = client.post(
        f"/{settings.PREFIX}api/reference/upload",
        data={
            "image": file_sm,
            "start": timezone.localdate(),
            "end": timezone.localdate(),
            "student_comment": "hi123",
        },
        format="multipart",
    )
    assert response.status_code == status.HTTP_200_OK
    response = client.post(
        f"/{settings.PREFIX}api/reference/upload",
        data={
            "image": file_lg,
            "start": timezone.localdate(),
            "end": timezone.localdate(),
            "student_comment": "hi123",
        },
        format="multipart",
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.data["code"] == ReferenceErrors.TOO_MUCH_UPLOADS_PER_DAY[0]
    settings.MAX_IMAGE_SIZE = 1000
    file_lg.seek(0)
    response = client.post(
        f"/{settings.PREFIX}api/reference/upload",
        data={
            "image": file_lg,
            "start": timezone.localdate(),
            "end": timezone.localdate(),
            "student_comment": "hi123",
        },
        format="multipart",
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.data["code"] == ReferenceErrors.TOO_MUCH_UPLOADS_PER_DAY[0]
    settings.MAX_IMAGE_SIZE = 5_000_000
    response = client.post(
        f"/{settings.PREFIX}api/reference/upload",
        data={
            "image": file_md,
            "start": timezone.localdate(),
            "end": timezone.localdate(),
            "student_comment": "hi123",
        },
        format="multipart",
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.data["code"] == ReferenceErrors.TOO_MUCH_UPLOADS_PER_DAY[0]
    assert Attendance.objects.count() == 0
    assert Training.objects.count() == 0
    assert Reference.objects.count() == 1
    ref = Reference.objects.get()
    assert ref.student == user.student
    assert ref.semester == semester
    assert ref.hours == 0

    ref.hours = 2
    ref.start = timezone.localdate()
    ref.end = timezone.localdate()
    ref.student_comment = "hi"
    ref.save()

    assert Attendance.objects.count() == 1
    assert Training.objects.count() == 1
    att = Attendance.objects.get()
    assert att.student == user.student
    assert att.hours == 2

    ref.hours = 3
    ref.start = timezone.localdate()
    ref.end = timezone.localdate()
    ref.student_comment = "hi1"
    ref.save()

    assert Attendance.objects.count() == 1
    assert Training.objects.count() == 1
    att = Attendance.objects.get()
    assert att.hours == 3

    # should fail to upload twice per day
    file_md.seek(0)
    response = client.post(
        f"/{settings.PREFIX}api/reference/upload",
        data={
            "image": file_md,
            "start": timezone.localdate(),
            "end": timezone.localdate(),
            "student_comment": "hi123",
        },
        format="multipart",
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.data["code"] == ReferenceErrors.TOO_MUCH_UPLOADS_PER_DAY[0]

    # should succeed on next day
    freezer.move_to(dtm.date(2020, 1, 3))

    file_md.seek(0)
    response = client.post(
        f"/{settings.PREFIX}api/reference/upload",
        data={
            "image": file_md,
            "start": timezone.localdate(),
            "end": timezone.localdate(),
            "student_comment": "hi123",
        },
        format="multipart",
    )
    assert response.status_code == status.HTTP_200_OK
    assert Attendance.objects.count() == 1
    assert Training.objects.count() == 1
    assert Reference.objects.count() == 2
