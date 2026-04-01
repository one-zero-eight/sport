from typing import Iterable

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from starlette import status

from accounts.models import User
from api_v3.dependencies import VerifiedDep
from api_v3.permissions import is_student, is_trainer, is_admin
from api_v3.utils.semester import get_current_semester
from sport.models import Group

router = APIRouter(
    tags=["Users"],
    responses={
        401: {"description": "Invalid token"},
        403: {"description": "Unauthorized"},
    },
)


class StudentInfoSchema(BaseModel):
    student_status: str
    medical_group: str


class GroupInfoSchema(BaseModel):
    id: int
    display_name: str


class TrainerInfoSchema(BaseModel):
    groups: list[GroupInfoSchema]


class UserSchema(BaseModel):
    user_id: int
    email: str
    full_name: str
    is_admin: bool
    student_info: StudentInfoSchema | None
    trainer_info: TrainerInfoSchema | None

    @classmethod
    def from_user(cls, user: User):
        student_info = None
        trainer_info = None

        if is_student(user):
            student_info = StudentInfoSchema(
                student_status=user.student_or_none.student_status.name,
                medical_group=user.student_or_none.medical_group.name,
            )

        if is_trainer(user):
            current_semester = get_current_semester()
            training_groups: Iterable[Group] = Group.objects.filter(
                semester__id=current_semester.id,
                trainers__pk=user.id,
            )
            trainer_info = TrainerInfoSchema(
                groups=[GroupInfoSchema(
                    id=group.id,
                    display_name=group.to_frontend_name(),
                ) for group in training_groups]
            )

        return UserSchema(
            user_id=user.id,
            email=user.email,
            full_name=user.get_full_name(),
            is_admin=is_admin(user),
            student_info=student_info,
            trainer_info=trainer_info,
        )


@router.get(
    "/users/me",
    responses={
        200: {"description": "Get user information"},
    },
)
def get_me(user: VerifiedDep) -> UserSchema:
    """
    Retrieve current user information.
    """
    return UserSchema.from_user(user)


@router.get(
    "/users/{user_id}",
    responses={
        200: {"description": "Get user information by ID"},
        404: {"description": "No such user found"},
    }
)
def get_user_by_id(current_user: VerifiedDep, user_id: int) -> UserSchema:
    """
    Retrieve user information by ID. Only for superuser.
    """
    if not is_admin(current_user):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You are not a superuser")

    try:
        user: User = User.objects.prefetch_related("student", "trainer").get(id=user_id)
    except User.DoesNotExist:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    return UserSchema.from_user(user)


@router.post(
    "/users/batch",
    responses={
        200: {"description": "Get many user information by ID"},
    }
)
def get_many_users(current_user: VerifiedDep, user_ids: list[int]) -> list[UserSchema]:
    """
    Retrieve user information by ID. Only for superuser.
    """
    if not is_admin(current_user):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You are not a superuser")

    users: Iterable[User] = User.objects.prefetch_related("student", "trainer").filter(id__in=user_ids)

    return [UserSchema.from_user(user) for user in users]
