from types import SimpleNamespace
from unittest.mock import patch
from urllib.parse import parse_qs, urlparse

import pytest
from django.test import RequestFactory
from django.urls import reverse

from sport.admin.attendanceAdmin import AttendanceAdmin
from sport.admin.referenceAdmin import ReferenceAdmin
from sport.admin.site import site
from sport.admin.trainingAdmin import TrainingAdmin
from sport.models import Attendance, Reference, Training


@pytest.mark.parametrize(
    ("admin_class", "model", "changelist_name", "filter_name"),
    (
        (
            AttendanceAdmin,
            Attendance,
            "admin:sport_attendance_changelist",
            "training__group__semester__id__exact",
        ),
        (
            ReferenceAdmin,
            Reference,
            "admin:sport_reference_changelist",
            "semester__id__exact",
        ),
        (
            TrainingAdmin,
            Training,
            "admin:sport_training_changelist",
            "group__semester__id__exact",
        ),
    ),
)
def test_semester_filter_does_not_accumulate_between_requests(
    admin_class,
    model,
    changelist_name,
    filter_name,
):
    model_admin = admin_class(model, site)
    changelist_url = reverse(changelist_name)
    request_factory = RequestFactory()

    def open_changelist(semester_id):
        request = request_factory.get(
            changelist_url,
            HTTP_REFERER="http://testserver/admin/sport/semester/add/",
        )
        with patch(
            "sport.admin.utils.get_ongoing_semester",
            return_value=SimpleNamespace(pk=semester_id),
        ):
            return model_admin.changelist_view(request)

    first_response = open_changelist(1)
    second_response = open_changelist(2)

    assert parse_qs(urlparse(first_response.url).query) == {filter_name: ["1"]}
    assert parse_qs(urlparse(second_response.url).query) == {filter_name: ["2"]}
