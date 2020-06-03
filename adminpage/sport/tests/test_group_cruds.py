import pytest
from datetime import date

from django.conf import settings

from sport.crud import get_clubs, get_student_groups, get_trainer_groups, get_sc_training_group
from sport.models import Student, Enroll, Trainer, Group


@pytest.mark.django_db
@pytest.mark.freeze_time('2020-01-20 10:03')
def test_enroll(student_factory, sport_factory, semester_factory, group_factory, enroll_factory):
    student_factory("A")
    student = Student.objects.get()
    sport = sport_factory(name="Sport")
    s1 = semester_factory(name="S19", start=date(2020, 1, 1), end=date(2020, 1, 3), choice_deadline=date(2020, 1, 2))
    s2 = semester_factory(name="S20", start=date(2020, 1, 4), end=date(2020, 1, 24), choice_deadline=date(2020, 1, 20))
    g1 = group_factory(name="G1", sport=sport, semester=s1, capacity=20, is_club=False)
    c1 = group_factory(name="C1", sport=sport, semester=s1, capacity=20, is_club=True)
    g2 = group_factory(name="G2", sport=sport, semester=s2, capacity=20, is_club=False)
    c2 = group_factory(name="C2", sport=sport, semester=s2, capacity=20, is_club=True)

    clubs = get_clubs()
    assert clubs == [{
        "id": c2.pk,
        "name": c2.name,
        "sport_name": sport.name,
        "semester": s2.name,
        "capacity": c2.capacity,
        "description": c2.description,
        "trainer_id": c2.trainer,
        "is_club": True,
        "current_load": 0
    }]

    enroll_factory(student=student, group=c2, is_primary=True)

    clubs = get_clubs()
    assert clubs == [{
        "id": c2.pk,
        "name": c2.name,
        "sport_name": sport.name,
        "semester": s2.name,
        "capacity": c2.capacity,
        "description": c2.description,
        "trainer_id": c2.trainer,
        "is_club": True,
        "current_load": 1
    }]

    Enroll.objects.all().delete()
    enroll_factory(student=student, group=g1, is_primary=False)
    enroll_factory(student=student, group=g2, is_primary=False)
    enroll_factory(student=student, group=c1, is_primary=False)
    enroll_factory(student=student, group=c2, is_primary=False)

    clubs = get_clubs()
    assert clubs == [{
        "id": c2.pk,
        "name": c2.name,
        "sport_name": sport.name,
        "semester": s2.name,
        "capacity": c2.capacity,
        "description": c2.description,
        "trainer_id": c2.trainer,
        "is_club": True,
        "current_load": 1
    }]


@pytest.mark.django_db
@pytest.mark.freeze_time('2020-01-20 10:03')
def test_get_student_trainer_groups(student_factory, trainer_factory, sport_factory, semester_factory, group_factory,
                                    enroll_factory):
    student_factory("A")
    trainer_factory("B")
    student = Student.objects.get()
    trainer = Trainer.objects.get()
    sport = sport_factory(name="Sport")
    s1 = semester_factory(name="S19", start=date(2020, 1, 1), end=date(2020, 1, 3), choice_deadline=date(2020, 1, 2))
    s2 = semester_factory(name="S20", start=date(2020, 1, 4), end=date(2020, 1, 24), choice_deadline=date(2020, 1, 20))
    g1 = group_factory(name="G1", sport=sport, semester=s1, capacity=20, is_club=False, trainer=trainer)
    c1 = group_factory(name="C1", sport=sport, semester=s1, capacity=20, is_club=True)
    g2 = group_factory(name="G2", sport=sport, semester=s2, capacity=20, is_club=False, trainer=trainer)
    c2 = group_factory(name="C2", sport=sport, semester=s2, capacity=20, is_club=True)

    enroll_factory(student=student, group=g1, is_primary=False)
    enroll_factory(student=student, group=c1, is_primary=True)
    enroll_factory(student=student, group=g2, is_primary=False)
    enroll_factory(student=student, group=c2, is_primary=True)

    student_groups = get_student_groups(student)
    trainer_groups = get_trainer_groups(trainer)

    assert student_groups == [
        {
            "id": c2.pk,
            "name": c2.name,
            "sport_name": sport.name,
            "is_primary": True
        },
        {
            "id": g2.pk,
            "name": g2.name,
            "sport_name": sport.name,
            "is_primary": False
        }
    ]

    assert trainer_groups == [{
        "id": g2.pk,
        "name": g2.name,
        "sport_name": sport.name
    }]


@pytest.mark.django_db
@pytest.mark.freeze_time('2020-01-20 10:03')
def test_get_sc_training_group(sport_factory, semester_factory, group_factory):
    semester_factory(name="S19", start=date(2020, 1, 1), end=date(2020, 1, 3), choice_deadline=date(2020, 1, 2))

    assert Group.objects.count() == 2

    s2 = semester_factory(name="S20", start=date(2020, 1, 4), end=date(2020, 1, 24), choice_deadline=date(2020, 1, 20))

    assert Group.objects.count() == 4

    sc_group2 = Group.objects.get(semester=s2, name=settings.SC_TRAINERS_GROUP_NAME)

    assert get_sc_training_group() == {
        "id": sc_group2.pk,
        "name": sc_group2.name,
        "sport_name": sc_group2.sport.name,
    }