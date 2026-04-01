import datetime

from django.conf import settings
from django.db.models import Count, Q
from django.utils import timezone
from fastapi import APIRouter, HTTPException, Query
from starlette import status

from api.crud.crud_training import can_check_in

from api_v3.dependencies import VerifiedDep
from api_v3.permissions import is_student, is_trainer, is_admin
from api_v3.routers.trainings import TrainingInfoSchema, TrainingInfoPersonalSchema
from api_v3.utils.semester import get_current_semester
from api_v3.utils.student_group_access import education_level_q_for_training_group
from sport.models import Training, TrainingCheckIn

router = APIRouter(
    tags=["Trainings schedule"],
    responses={
        401: {"description": "Invalid token"},
        403: {"description": "Unauthorized"},
    },
)


@router.get(
    "/users/me/schedule",
    responses={
        200: {"description": "Get personal schedule"},
    },
)
def get_personal_schedule(
    user: VerifiedDep,
    start: datetime.datetime = Query(..., description="Start datetime"),
    end: datetime.datetime = Query(..., description="End datetime"),
) -> list[TrainingInfoPersonalSchema]:
    """
    Retrieve personal training schedule for the current user (student or trainer).
    """
    if not (is_student(user) or is_trainer(user)):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not allowed to view personal schedule",
        )

    if start >= end:
        start, end = end, start

    semester = get_current_semester()

    student_trainings: list[TrainingInfoPersonalSchema] = []
    trainer_trainings: list[TrainingInfoPersonalSchema] = []
    now_local = timezone.localtime()

    if is_trainer(user):
        trainer = user.trainer_or_none
        trainings = (
            Training.objects.select_related("group", "group__sport", "training_class")
            .annotate(load=Count("checkins"))
            .filter(
                group__semester__id=semester.id,
                group__trainers=trainer,
            )
            .filter(
                Q(start__gt=start, start__lt=end)
                | Q(end__gt=start, end__lt=end)
                | Q(start__lt=start, end__gt=end)
            )
        )
        for t in trainings:
            start_dt = timezone.localtime(t.start)
            training = TrainingInfoSchema.from_model(t)
            trainer_trainings.append(
                TrainingInfoPersonalSchema(
                    training=training,
                    checked_in=False,
                    can_check_in=False,
                    can_grade=True,
                    can_edit=start_dt <= now_local <= start_dt + settings.TRAINING_EDITABLE_INTERVAL,
                )
            )

    if is_student(user):
        student = user.student_or_none
        trainings = (
            Training.objects.select_related("group", "group__sport", "training_class")
            .prefetch_related("group__allowed_medical_groups", "checkins")
            .annotate(load=Count("checkins"))
            .filter(
                (
                    Q(start__range=(start, end))
                    | Q(end__range=(start, end))
                    | (Q(start__lte=start) & Q(end__gte=end))
                ),
                ~Q(group__sport=None),
                education_level_q_for_training_group(student),
                (
                    Q(group__allowed_medical_groups=student.medical_group)
                    | Q(group__allowed_students=student.pk)
                ),
                group__semester=semester.id,
            )
            .exclude(group__banned_students=student.pk)
            .distinct()
        )
        student_checkins = list(
            TrainingCheckIn.objects.filter(
                student=student,
                training__start__range=(start, end),
            ).select_related("training", "training__group__sport")
        )
        student_checkins_map = {c.training_id: c for c in student_checkins}
        time_now = timezone.now()

        for t in trainings:
            start_dt = timezone.localtime(t.start)
            training = TrainingInfoSchema.from_model(t)
            student_trainings.append(
                TrainingInfoPersonalSchema(
                    training=training,
                    checked_in=t.id in student_checkins_map,
                    can_check_in=can_check_in(student, t, student_checkins, time_now),
                    can_grade=False,
                    can_edit=start_dt <= now_local <= start_dt + settings.TRAINING_EDITABLE_INTERVAL,
                )
            )

    trainings_by_id: dict[int, TrainingInfoPersonalSchema] = {}
    for ev in trainer_trainings:
        trainings_by_id[ev.training.id] = ev
    for ev in student_trainings:
        if ev.training.id in trainings_by_id:
            trainings_by_id[ev.training.id] = trainings_by_id[ev.training.id].model_copy(
                update=dict(checked_in=ev.checked_in, can_check_in=ev.can_check_in)
            )
        else:
            trainings_by_id[ev.training.id] = ev

    return sorted(trainings_by_id.values(), key=lambda x: x.start)


@router.get(
    "/sports/{sport_id}/schedule",
    responses={
        200: {"description": "Get sport schedule"},
    },
)
def get_sport_schedule(
    user: VerifiedDep,
    sport_id: int,
    start: datetime.datetime = Query(..., description="Start datetime"),
    end: datetime.datetime = Query(..., description="End datetime"),
) -> list[TrainingInfoSchema]:
    """
    Retrieve training schedule for a specific sport.
    """
    if not (is_student(user) or is_trainer(user) or is_admin(user)):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not allowed to view schedule",
        )

    if start >= end:
        start, end = end, start

    query = (
        Training.objects.select_related("group", "group__sport", "training_class")
        .filter(start__gte=start, end__lte=end, group__sport__id=sport_id)
        .annotate(
            load=Count("checkins", distinct=True),
        )
    )
    query = query.order_by("start")

    return [
        TrainingInfoSchema.from_model(t)
        for t in query
    ]
