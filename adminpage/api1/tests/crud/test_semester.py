import pytest
from datetime import date

from api.crud import get_ongoing_semester


@pytest.mark.django_db
def test_get_ongoing_semester(semester_factory):
    semester_factory(name="S19", start=date(2020, 1, 1), end=date(2020, 1, 3))
    s2 = semester_factory(name="S20", start=date(2020, 1, 4), end=date(2020, 1, 24))

    assert get_ongoing_semester() == s2
