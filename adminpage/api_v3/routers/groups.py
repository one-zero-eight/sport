from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from starlette import status
from django.utils.html import strip_tags

from api_v3.dependencies import VerifiedDep
from api_v3.utils.semester import get_current_semester
from sport.models import Group, Sport

router = APIRouter(
    tags=["Sport groups"],
    responses={
        401: {"description": "Invalid token"},
        403: {"description": "Unauthorized"},
    },
)


class TrainerSchema(BaseModel):
    id: int
    email: str
    full_name: str


class GroupInfoSchema(BaseModel):
    id: int

    display_name: str
    sport_name: str | None
    group_name: str | None

    capacity: int
    is_accredited: bool
    is_club: bool
    is_paid: bool
    sport_id: int | None
    sport_description: str
    trainers: list[TrainerSchema]
    allowed_medical_groups: list[str]
    allowed_education_level: int


class ShortSportGroupSchema(BaseModel):
    id: int
    display_name: str
    group_name: str | None
    capacity: int
    is_accredited: bool
    is_club: bool
    is_paid: bool
    trainers: list[TrainerSchema]
    allowed_medical_groups: list[str]
    allowed_education_level: int


class DetailedSportSchema(BaseModel):
    id: int
    name: str
    description: str
    groups: list[ShortSportGroupSchema]


def _get_group_trainers(group: Group) -> list[TrainerSchema]:
    return [TrainerSchema(
        id=t.user.id,
        email=t.user.email,
        full_name=t.user.get_full_name(),
    ) for t in group.trainers.all()]


@router.get(
    "/sports",
    responses={
        200: {"description": "Get available sports with detailed groups information"},
    },
)
def list_sports(_user: VerifiedDep) -> list[DetailedSportSchema]:
    """
    Retrieve list of all available sports with their groups and schedules.
    """
    current_semester = get_current_semester()
    groups = Group.objects.filter(semester__pk=current_semester.pk)

    sports = Sport.objects.filter(
        id__in=groups.values_list("sport", flat=True)
    ).filter(special=False, visible=True).distinct()

    sports_list = []
    for sport in sports:
        sport_groups = groups.filter(sport=sport).select_related(
            "trainer__user", "sport"
        ).prefetch_related("trainers__user", "schedule", "allowed_medical_groups")

        groups_data = []
        for group in sport_groups:
            groups_data.append(
                ShortSportGroupSchema(
                    id=group.id,
                    display_name=group.to_frontend_name(),
                    group_name=group.name,
                    capacity=group.capacity,
                    is_accredited=group.accredited,
                    is_club=group.is_club,
                    is_paid=group.is_paid,
                    trainers=_get_group_trainers(group),
                    allowed_medical_groups=[
                        mg.name for mg in group.allowed_medical_groups.all()
                    ],
                    allowed_education_level=group.allowed_education_level,
                )
            )

        sports_list.append(
            DetailedSportSchema(
                id=sport.id,
                name=strip_tags(sport.name) if sport.name else "",
                description=strip_tags(sport.description) if sport.description else "",
                groups=groups_data,
            )
        )
    return sports_list


@router.get(
    "/sport-groups/{group_id}",
    responses={
        200: {"description": "Get sport group information"},
        404: {"description": "Group not found"},
    },
)
def get_group_info_view(_user: VerifiedDep, group_id: int) -> GroupInfoSchema:
    """
    Retrieve detailed information about a sport group.
    """
    current_semester = get_current_semester()
    try:
        group = (
            Group.objects.select_related("sport", "semester")
            .prefetch_related("trainers__user", "allowed_medical_groups")
            .get(id=group_id, semester=current_semester)
        )
    except Group.DoesNotExist:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Group not found",
        )

    return GroupInfoSchema(
        id=group.id,
        display_name=group.to_frontend_name(),
        group_name=group.name,
        capacity=group.capacity,
        is_accredited=group.accredited,
        is_club=group.is_club,
        is_paid=group.is_paid,
        sport_id=group.sport_id,
        sport_name=group.sport.name if group.sport else None,
        trainers=_get_group_trainers(group),
        sport_description=group.sport.description if group.sport and group.sport.description else "",
        allowed_medical_groups=[mg.name for mg in group.allowed_medical_groups.all()],
        allowed_education_level=group.allowed_education_level,
    )
