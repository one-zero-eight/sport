import unittest
from datetime import date

import pytest
from django.conf import settings
from django.forms.models import model_to_dict

from api.crud import get_student_groups, get_trainer_groups, get_sports
from sport.models import Enroll, Group, MedicalGroups

assertMembers = unittest.TestCase().assertCountEqual


@pytest.mark.django_db
@pytest.mark.freeze_time('2020-01-02 10:03')
def test_sport(
        student_factory,
        sport_factory,
        semester_factory,
        group_factory,
):
    student_factory("A@foo.bar")
    sport = sport_factory(name="Sport")
    s1 = semester_factory(name="S19", start=date(2020, 1, 1), end=date(2020, 1, 3))
    group_factory(name="C1", sport=sport, semester=s1, capacity=20)
    group_factory(name="C2", sport=sport, semester=s1, capacity=20)

    sport_list = get_sports()

    valid = model_to_dict(sport)
    valid['trainers'] = []
    valid['num_of_groups'] = 2
    valid['free_places'] = 40

    assert list(sport_list) == [
        valid,
    ]


@pytest.mark.django_db
@pytest.mark.freeze_time('2020-01-05 10:03')
def test_sports_in_new_empty_semester(
        student_factory,
        sport_factory,
        semester_factory,
        group_factory,
):
    student_factory("A@foo.bar")
    sport = sport_factory(name="Sport")
    s1 = semester_factory(name="S1", start=date(2020, 1, 1), end=date(2020, 1, 3))
    group_factory(name="C1", sport=sport, semester=s1, capacity=20)
    group_factory(name="C2", sport=sport, semester=s1, capacity=20)

    semester_factory(name="S2", start=date(2020, 1, 4), end=date(2020, 1, 7))

    sport_list = get_sports()
    assert len(list(sport_list)) == 0


@pytest.mark.django_db
@pytest.mark.freeze_time('2020-01-05 10:03')
def test_sports_in_new_filled_semester(
        student_factory,
        sport_factory,
        semester_factory,
        group_factory,
):
    student_factory("A@foo.bar")
    sport = sport_factory(name="Sport")
    s1 = semester_factory(name="S1", start=date(2020, 1, 1), end=date(2020, 1, 3))
    group_factory(name="C1", sport=sport, semester=s1, capacity=20)
    group_factory(name="C2", sport=sport, semester=s1, capacity=20)

    sport1 = sport_factory(name="Sport1")
    s2 = semester_factory(name="S2", start=date(2020, 1, 4), end=date(2020, 1, 7))
    group_factory(name="C1", sport=sport1, semester=s2, capacity=20)

    sport_list = get_sports()

    valid = model_to_dict(sport1)
    valid['trainers'] = []
    valid['free_places'] = 20
    valid['num_of_groups'] = 1

    assert list(sport_list) == [
        valid,
    ]


@pytest.mark.django_db
@pytest.mark.freeze_time('2020-01-20 10:03')
def test_sport_no_appropriate_group_in_sport(
        student_factory,
        sport_factory,
        semester_factory,
        group_factory,
):
    student = student_factory("A@foo.bar").student
    student.medical_group_id = MedicalGroups.NO_CHECKUP

    sport = sport_factory(name="Sport")
    s1 = semester_factory(name="S19", start=date(2020, 1, 1), end=date(2020, 1, 3))
    group_factory(name="C1", sport=sport, semester=s1, capacity=20)
    group_factory(name="C2", sport=sport, semester=s1, capacity=20)

    sport_list = get_sports(student=student)
    assert len(sport_list) == 0


@pytest.mark.django_db
@pytest.mark.freeze_time('2020-01-20 10:03')
def test_get_student_trainer_groups(
        student_factory,
        trainer_factory,
        sport_factory,
        semester_factory,
        group_factory,
        enroll_factory
):
    student = student_factory("A@foo.bar").student
    trainer = trainer_factory("B@foo.bar").trainer
    sport = sport_factory(name="Sport")
    s1 = semester_factory(name="S19", start=date(2020, 1, 1), end=date(2020, 1, 3))
    s2 = semester_factory(name="S20", start=date(2020, 1, 4), end=date(2020, 1, 24))
    g1 = group_factory(name="G1", sport=sport, semester=s1, capacity=20, is_club=False, trainer=trainer)
    c1 = group_factory(name="C1", sport=sport, semester=s1, capacity=20, is_club=True)
    g2 = group_factory(name="G2", sport=sport, semester=s2, capacity=20, is_club=False, trainer=trainer)
    c2 = group_factory(name="C2", sport=sport, semester=s2, capacity=20, is_club=True)

    enroll_factory(student=student, group=g1, )
    enroll_factory(student=student, group=c1, )
    enroll_factory(student=student, group=g2, )
    enroll_factory(student=student, group=c2, )

    student_groups = get_student_groups(student)
    trainer_groups = get_trainer_groups(trainer)

    # FIXME: DEPRECATED!!!!!!!!!!!!
    assertMembers(student_groups, [
        {
            "id": c2.pk,
            "name": c2.name,
            "sport_name": sport.name,
        },
        {
            "id": g2.pk,
            "name": g2.name,
            "sport_name": sport.name,
        }
    ])

    assert list(trainer_groups) == [{
        "id": g2.pk,
        "name": g2.to_frontend_name()
    }]
