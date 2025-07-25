from typing import Optional, Tuple

import pytest
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import (
    Group
)


@pytest.fixture
@pytest.mark.django_db
def student_group() -> Group:
    group, created = Group.objects.get_or_create(
        verbose_name=settings.STUDENT_AUTH_GROUP_VERBOSE_NAME,
        defaults={
            "name": settings.STUDENT_AUTH_GROUP_NAME,
        }
    )
    return group


@pytest.fixture
@pytest.mark.django_db
def trainer_group() -> Group:
    group, created = Group.objects.get_or_create(
        verbose_name=settings.TRAINER_AUTH_GROUP_VERBOSE_NAME,
        defaults={
            "name": settings.TRAINER_AUTH_GROUP_NAME,
        }
    )
    return group


def create_user_in_groups(
        predefined_groups: Tuple[Group] = (),
):
    def create_app_user(
            email: str,
            password: Optional[str] = None,
            first_name: Optional[str] = "first name",
            last_name: Optional[str] = "last name",
            is_staff: str = False,
            is_superuser: str = False,
            is_active: str = True,
            groups: Tuple[Group] = (),
    ):
        user = get_user_model().objects.create_user(
            password=password,
            first_name=first_name,
            last_name=last_name,
            email=email,
            is_staff=is_staff,
            is_superuser=is_superuser,
            is_active=is_active,
        )
        user.groups.add(*groups)
        user.groups.add(*predefined_groups)
        return user

    return create_app_user


@pytest.fixture
def user_factory():
    return create_user_in_groups()


@pytest.fixture
def student_factory(student_group):
    return create_user_in_groups(
        predefined_groups=(student_group,)
    )


@pytest.fixture
def trainer_factory(trainer_group):
    return create_user_in_groups(
        predefined_groups=(trainer_group,)
    )