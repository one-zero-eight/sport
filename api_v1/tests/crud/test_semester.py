import datetime as dtm

import pytest

from api_v1.crud import get_ongoing_semester


@pytest.mark.django_db
def test_get_ongoing_semester(semester_factory):
    semester_factory(name="S19", start=dtm.date(2020, 1, 1), end=dtm.date(2020, 1, 3))
    s2 = semester_factory(name="S20", start=dtm.date(2020, 1, 4), end=dtm.date(2020, 1, 24))

    assert get_ongoing_semester() == s2
