from collections import defaultdict

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from starlette import status

from api_v3.dependencies import VerifiedDep
from sport.models import TrainingClass, MedicalGroup, FAQElement, StudentStatus

router = APIRouter(
    tags=["Info"],
    responses={
        401: {"description": "Invalid token"},
        403: {"description": "Unauthorized"},
    },
)


class TrainingLocationSchema(BaseModel):
    id: int
    name: str


@router.get(
    "/training-locations",
    responses={
        200: {"description": "Get training locations"},
    },
)
def list_training_locations(_user: VerifiedDep) -> list[TrainingLocationSchema]:
    """
    Retrieve list of all training classes.
    """
    classes = list(TrainingClass.objects.all())
    return [
        TrainingLocationSchema.model_validate(c, from_attributes=True) for c in classes
    ]


class MedicalGroupSchema(BaseModel):
    id: int
    name: str
    description: str


@router.get(
    "/medical-groups",
    responses={
        200: {"description": "Get medical groups"},
    },
)
def list_medical_groups(_user: VerifiedDep) -> list[MedicalGroupSchema]:
    """
    Retrieve list of all medical groups.
    """
    medical_groups = MedicalGroup.objects.all()
    return [
        MedicalGroupSchema.model_validate(mg, from_attributes=True)
        for mg in medical_groups
    ]


type FAQResponse = dict[str, dict[str, str]]


@router.get(
    "/faq",
    responses={
        200: {
            "description": "FAQ grouped by category",
            "content": {
                "application/json": {
                    "example": {"General": {"What is this?": "This is an FAQ."}}
                }
            },
        },
    },
)
def get_faq(_user: VerifiedDep) -> FAQResponse:
    """
    Returns FAQ as:
    {
      "Category name": {
          "Question 1": "Answer 1",
          "Question 2": "Answer 2"
      },
      ...
    }
    """
    rows = (
        FAQElement.objects.select_related("category")
        .values_list("category__name", "question", "answer")
        .order_by("category__name", "id")
    )

    result = defaultdict(dict)
    for cat_name, q, a in rows:
        result[cat_name][q] = a

    return result



class StudentStatusSchema(BaseModel):
    id: int
    name: str
    description: str


@router.get(
    "/student-statuses",
    responses={
        200: {"description": "Get all student statuses"},
        404: {"description": "No student statuses found"},
    },
)
def get_student_statuses(_user: VerifiedDep) -> list[StudentStatusSchema]:
    """
    Retrieve a list of all possible student statuses.
    """
    statuses = list(StudentStatus.objects.all())
    if not statuses:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No student statuses found",
        )
    return [
        StudentStatusSchema.model_validate(s, from_attributes=True) for s in statuses
    ]
