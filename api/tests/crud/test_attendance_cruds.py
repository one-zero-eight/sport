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


@pytest.mark.django_db
def test_hours_statistics(student_factory, sport_factory, semester_factory, group_factory, training_factory, attendance_factory):
    student = student_factory("A").student
    other_student = student_factory("B").student
    student.enrollment_year = 2000
    student.save()
    sport = sport_factory(name="Sport")
    s1 = semester_factory(name="S19", start=date(2020, 1, 1), end=date(2020, 2, 1))
    s2 = semester_factory(name="S20", start=date(2020, 3, 1), end=date(2020, 4, 1))
    g11 = group_factory(name="G11", sport=sport, semester=s1, capacity=20)
    g12 = group_factory(name="G12", sport=sport, semester=s1, capacity=20)
    g21 = group_factory(name="G21", sport=sport, semester=s2, capacity=20)
    g22 = group_factory(name="G22", sport=sport, semester=s2, capacity=20)

    trainings = []
    for i, g in enumerate([g11, g12, g21, g22]):
        t = training_factory(group=g, start=timezone.now(), end=timezone.now())
        trainings.append(t)
        attendance_factory(training=t, student=student, hours=i + 1)
        attendance_factory(training=t, student=other_student, hours=1)
    brief = get_brief_hours(student)

    assertMembers(brief, [
        {
            "hours": 3,
            "semester_id": s1.pk,
            "semester_name": s1.name,
            'semester_start': s1.start.strftime("%b. %d, %Y"),
            'semester_end': s1.end.strftime("%b. %d, %Y"),
        },
        {
            "hours": 7,
            "semester_id": s2.pk,
            "semester_name": s2.name,
            'semester_start': s2.start.strftime("%b. %d, %Y"),
            'semester_end': s2.end.strftime("%b. %d, %Y"),
        }
    ])
    stat1 = get_detailed_hours(student, s1)
    stat2 = get_detailed_hours(student, s2)
    assertMembers(stat1, [
        {
            "group": g12.name,
            "custom_name": None,
            "timestamp": trainings[1].start,
            "hours": 2
        },
        {
            "group": g11.name,
            "custom_name": None,
            "timestamp": trainings[0].start,
            "hours": 1
        }
    ])
    assertMembers(stat2, [
        {
            "group": g22.name,
            "custom_name": None,
            "timestamp": trainings[3].start,
            "hours": 4
        },
        {
            "group": g21.name,
            "custom_name": None,
            "timestamp": trainings[2].start,
            "hours": 3
        }
    ])
