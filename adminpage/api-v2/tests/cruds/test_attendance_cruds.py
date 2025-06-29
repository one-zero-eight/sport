import pytest
import unittest
from datetime import date
from django.utils import timezone

from api.crud import get_detailed_hours, get_brief_hours, mark_hours
from sport.models import Attendance

dummy_date = date(2020, 1, 1)

assertMembers = unittest.TestCase().assertCountEqual

@pytest.mark.django_db
def test_mark_hours(student_factory, sport_factory, semester_factory, group_factory, training_factory):
    student1 = student_factory("A@foo.bar").student
    student2 = student_factory("B@foo.bar").student
    sport = sport_factory(name="Sport")
    semester = semester_factory(name="S19", start=dummy_date, end=dummy_date)
    group = group_factory(name="G1", sport=sport, semester=semester, capacity=20)
    training = training_factory(group=group, start=timezone.now(), end=timezone.now())
    mark_hours(training, [
        (student1.pk, 1),
        (student2.pk, 2)
    ])
    attendance1 = Attendance.objects.get(student=student1)
    attendance2 = Attendance.objects.get(student=student2)
    assert attendance1.hours == 1
    assert attendance2.hours == 2
    mark_hours(training, [
        (student1.pk, 3),
        (student2.pk, 0)
    ])
    attendance1 = Attendance.objects.get(student=student1)
    assert attendance1.hours == 3
    assert Attendance.objects.count() == 1
