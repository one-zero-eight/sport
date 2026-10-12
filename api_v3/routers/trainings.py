import datetime

import pglock
from django.db import IntegrityError
from django.db.models import Count
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from starlette import status

from django.utils import timezone

from api.crud.crud_training import can_check_in

from api_v3.dependencies import VerifiedDep
from api_v3.permissions import is_student, is_trainer, is_admin
from api_v3.routers.info import TrainingLocationSchema
from sport.models import Training, TrainingCheckIn, Student, CheckoutHistory

router = APIRouter(
    tags=["Trainings"],
    responses={
        401: {"description": "Invalid token"},
        403: {"description": "Unauthorized"},
    },
)


class TrainingInfoSchema(BaseModel):
    id: int
    start: datetime.datetime
    end: datetime.datetime
    is_all_day: bool
    training_location: TrainingLocationSchema | None

    display_name: str
    sport_name: str | None
    group_name: str | None
    training_custom_name: str | None

    is_accredited: bool
    is_club: bool
    is_paid: bool
    sport_id: int | None
    group_id: int

    checkins_count: int
    "How many students have checked in to this training."
    max_checkins: int
    "Capacity of this group, maximum available number of places to check in."

    @classmethod
    def from_model(cls, obj: Training):
        # obj must include 'load'
        return TrainingInfoSchema(
            id=obj.id,
            start=obj.start,
            end=obj.end,
            is_all_day=(
                obj.start.time() == datetime.time(0, 0, 0)
                and obj.end.time() == datetime.time(23, 59, 59)
            ),
            training_location=TrainingLocationSchema.model_validate(obj.training_class, from_attributes=True) if obj.training_class else None,

            display_name=obj.custom_name or obj.group.to_frontend_name(),
            sport_name=obj.group.sport.name if obj.group.sport else None,
            group_name=obj.group.name,
            training_custom_name=obj.custom_name,

            is_accredited=obj.group.accredited,
            is_club=obj.group.is_club,
            is_paid=obj.group.is_paid,
            sport_id=obj.group.sport_id,
            group_id=obj.group_id,

            checkins_count=obj.load,
            max_checkins=obj.group.capacity,
        )


class TrainingInfoPersonalSchema(BaseModel):
    training: TrainingInfoSchema
    checked_in: bool
    can_check_in: bool
    can_grade: bool
    can_edit: bool


@router.get(
    "/trainings/{training_id}",
    responses={
        200: {"description": "Get training information"},
        404: {"description": "Training not found"},
    },
)
def get_training_info(user: VerifiedDep, training_id: int) -> TrainingInfoSchema:
    """
    Retrieve detailed information about a specific training session.
    """
    if not (is_student(user) or is_trainer(user) or is_admin(user)):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not allowed to view trainings",
        )

    try:
        training = (
            Training.objects
            .select_related("group", "group__sport", "training_class")
            .annotate(
                load=Count("checkins", distinct=True),
            )
            .get(pk=training_id)
        )
    except Training.DoesNotExist:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Training with id={training_id} not found",
        )

    return TrainingInfoSchema.from_model(training)


@router.post(
    "/trainings/{training_id}/checkin",
    responses={
        200: {"description": "Check-in or cancel check-in"},
        400: {"description": "Invalid check-in operation"},
        404: {"description": "Training not found"},
    },
)
def training_checkin(
    user: VerifiedDep,
    training_id: int,
    checkin: bool = Query(
        ...,
        description="True - check in; False - cancel check-in",
    ),
    student_id: int | None = Query(
        None,
        description="Student ID if a trainer wants to cancel check in for some student",
    ),
) -> None:
    """
    Check-in or cancel check-in for a training.
    """
    if not is_student(user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only students can check in",
        )

    try:
        training = Training.objects.select_related("group", "group__sport").get(
            pk=training_id
        )
    except Training.DoesNotExist:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Training with id={training_id} not found",
        )
    student: Student = user.student_or_none

    already_checked_in = TrainingCheckIn.objects.filter(
        student=student, training=training
    ).exists()

    if not checkin:
        if not already_checked_in:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="You are not checked in at this training",
            )
        if training.end < timezone.now():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="You cannot cancel check-in for a finished training",
            )
        with pglock.advisory("check-in-lock"):  # Handle race condition
            checkin_obj = TrainingCheckIn.objects.get(student=student, training=training)
            CheckoutHistory.from_checkin(checkin_obj, CheckoutHistory.Reason.STUDENT_CANCEL)
            checkin_obj.delete()
        return None

    if already_checked_in:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You have already checked in at this training",
        )

    with pglock.advisory("check-in-lock"):  # Handle race condition
        if not can_check_in(student, training):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="You cannot check in at this training",
            )
        try:
            TrainingCheckIn.objects.create(student=student, training=training)
        except IntegrityError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="You have already checked in at this training",
            )

    return None
