import datetime

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from starlette import status

from api_v3.dependencies import VerifiedDep
from api_v3.utils.semester import get_current_semester
from sport.models import Semester

router = APIRouter(
    tags=["Semesters"],
    responses={
        401: {"description": "Invalid token"},
        403: {"description": "Unauthorized"},
    },
)


class SemesterSchema(BaseModel):
    id: int
    name: str
    start: datetime.date
    end: datetime.date
    required_hours: int = Field(..., validation_alias="hours")


@router.get(
    "/semesters",
    responses={
        200: {"description": "Get semesters information"},
        404: {"description": "No semesters found"},
    },
)
def get_semesters(_user: VerifiedDep) -> list[SemesterSchema]:
    """
    Retrieve all semesters information.
    """
    semesters = list(Semester.objects.all().order_by("-start", "-id"))
    if not semesters:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No semesters found",
        )
    return [SemesterSchema.model_validate(s, from_attributes=True) for s in semesters]


@router.get(
    "/semesters/current",
    responses={
        200: {"description": "Get current semester information"},
    },
)
def get_current_semester_route(_user: VerifiedDep) -> SemesterSchema:
    """
    Retrieve current semester information.
    """
    semester = get_current_semester()
    return SemesterSchema.model_validate(semester, from_attributes=True)


@router.get(
    "/semesters/{semester_id}",
    responses={
        200: {"description": "Get semester information via id"},
        404: {"description": "Semester not found"},
    },
)
def get_semester_by_id(_user: VerifiedDep, semester_id: int) -> SemesterSchema:
    """
    Retrieve semester information by ID.
    """
    semester = Semester.objects.filter(pk=semester_id).first()
    if not semester:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Semester not found",
        )
    return SemesterSchema.model_validate(semester, from_attributes=True)

