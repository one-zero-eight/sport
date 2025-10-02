from datetime import datetime, time, date
from typing import Optional, List

import pytest

from sport.models import (
    Attendance,
    Enroll,
    Group,
    Schedule,
    Semester,
    Sport,
    Student,
    Trainer,
    Training,
    TrainingClass,
    MedicalGroups,
)


@pytest.fixture
@pytest.mark.django_db
def semester_factory():
    def create_semester(
            name: str,
            start: date,
            end: date,
    ) -> Semester:
        obj, _ = Semester.objects.get_or_create(
            name=name,
            defaults={
                "start": start,
                "end": end,
            }
        )
        return obj

    return create_semester


@pytest.fixture
@pytest.mark.django_db
def sport_factory():
    def create_sport(
            name: str,
            special: bool = False,
    ) -> Sport:
        obj, _ = Sport.objects.get_or_create(
            name=name,
            defaults={
                "special": special,
            }
        )
        return obj

    return create_sport


@pytest.fixture
@pytest.mark.django_db
def group_factory():
    def create_group(
            name: str,
            capacity: int,
            sport: Sport,
            semester: Semester,

            trainer: Optional[Trainer] = None,
            description: Optional[str] = None,
            is_club: bool = False,
            allowed_medical_groups: Optional[List[MedicalGroups]] = None,
    ) -> Group:
        if allowed_medical_groups is None:
            allowed_medical_groups = [
                MedicalGroups.GENERAL,
                MedicalGroups.PREPARATIVE,
                MedicalGroups.SPECIAL1,
            ]

        obj, created = Group.objects.get_or_create(
            name=name,
            semester=semester,
            defaults={
                "capacity": capacity,
                "sport": sport,
                "is_club": is_club,
            }
        )

        if created is True:
            obj.allowed_medical_groups.set(allowed_medical_groups)

        if trainer is not None and not obj.trainers.filter(pk=trainer.pk).exists():
            obj.trainers.add(trainer)
            obj.save()
        return obj

    return create_group


@pytest.fixture
@pytest.mark.django_db
def schedule_factory():
    def create_schedule(
            group: Group,
            weekday: Schedule.Weekday,
            start: time,
            end: time,
            training_class: Optional[TrainingClass] = None,
    ) -> Schedule:
        obj, _ = Schedule.objects.get_or_create(
            group=group,
            weekday=weekday,
            start=start,
            end=end,
            defaults={
                "training_class": training_class,
            }
        )
        return obj

    return create_schedule


@pytest.fixture
@pytest.mark.django_db
def training_class_factory():
    def create_training_class(
            name: str
    ) -> TrainingClass:
        obj, _ = TrainingClass.objects.get_or_create(
            name=name,
        )
        return obj

    return create_training_class


@pytest.fixture
@pytest.mark.django_db
def training_factory():
    def create_training(
            group: Group,
            start: datetime,
            end: datetime,
            schedule: Optional[Schedule] = None,
            training_class: Optional[TrainingClass] = None
    ) -> Training:
        obj, _ = Training.objects.get_or_create(
            group=group,
            start=start,
            end=end,
            schedule=schedule,
            training_class=training_class,
        )
        return obj

    return create_training


@pytest.fixture
@pytest.mark.django_db
def enroll_factory():
    def create_enroll(
            student: Student,
            group: Group
    ):
        obj, _ = Enroll.objects.get_or_create(
            student=student,
            group=group
        )
        return obj

    return create_enroll


@pytest.fixture
@pytest.mark.django_db
def attendance_factory():
    def create_attendance(
            student: Student,
            training: Training,
            hours: float,
    ):
        obj, _ = Attendance.objects.get_or_create(
            student=student,
            training=training,
            hours=hours,
        )
        return obj

    return create_attendance
