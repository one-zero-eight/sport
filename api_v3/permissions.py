from accounts.models import User
from sport.models import Group


def is_student(user: User) -> bool:
    return user.student_or_none and user.student_or_none.student_status.name == "Normal"


def is_trainer(user: User) -> bool:
    return user.trainer_or_none is not None


def is_trainer_of_group(user: User, group: Group) -> bool:
    return is_trainer(user) and group.trainers.filter(pk=user.pk).exists()


def is_admin(user: User) -> bool:
    return user.is_staff or user.is_superuser
