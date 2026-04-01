import datetime
from typing import Any

from django.core.files.base import ContentFile
from django.db import transaction
from django.utils.timezone import make_naive
from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from pydantic import BaseModel, Field
from starlette import status

from api_v3.dependencies import VerifiedDep
from api_v3.utils.semester import get_current_semester
from api_v3.permissions import is_student
from sport.models import (
    MedicalGroupReference,
    MedicalGroupReferenceImage,
    Reference,
)

router = APIRouter(
    tags=["References"],
    responses={
        401: {"description": "Invalid token"},
        403: {"description": "Unauthorized"},
    },
)


class ReferenceUploadResponseSchema(BaseModel):
    id: int
    student_id: int
    semester: int = Field(validation_alias="semester_id")
    hours: int
    start: datetime.date
    end: datetime.date
    uploaded: Any
    message: str = "Medical certificate uploaded successfully"


class MedicalGroupReferenceUploadResponseSchema(BaseModel):
    id: int
    student_id: int
    semester: int = Field(validation_alias="semester_id")
    uploaded: Any


class ReferenceErrors:
    TOO_MUCH_UPLOADS_PER_DAY = (
        3,
        "Only 1 reference upload per day is allowed",
    )


@router.post(
    "/references/medical-leave",
    responses={
        200: {"description": "Upload medical certificate"},
        400: {"description": "Too many uploads per day or invalid data"},
    },
)
def reference_upload(
    user: VerifiedDep,
    image: UploadFile = File(...),
    start: datetime.date = Form(...),
    end: datetime.date = Form(...),
    student_comment: str | None = Form(None),
) -> ReferenceUploadResponseSchema:
    """
    Upload a medical certificate for sick leave. Only one upload per day is allowed.
    """
    if not is_student(user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only students can upload references",
        )

    semester = get_current_semester()

    try:
        with transaction.atomic():
            ref = Reference(
                start=start,
                end=end,
                student_comment=student_comment or "",
                semester=semester,
                student_id=user.pk,
                hours=(
                    (end - start).days // 7
                    * semester.number_hours_one_week_ill
                ),
            )
            ref.image.save(image.filename, ContentFile(image.file.read()), save=True)

            count = Reference.objects.filter(
                student_id=user.pk,
                uploaded__date=make_naive(ref.uploaded).date(),
            ).count()
            assert count == 1
    except AssertionError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=ReferenceErrors.TOO_MUCH_UPLOADS_PER_DAY[1],
        )

    return ReferenceUploadResponseSchema.model_validate(ref, from_attributes=True)


@router.post(
    "/references/medical-group",
    responses={
        200: {"description": "Upload medical group reference"},
        400: {"description": "Invalid data"},
    },
    openapi_extra={
        "requestBody": {
            "content": {
                "multipart/form-data": {
                    "schema": {
                        "type": "object",
                        "required": ["images"],
                        "properties": {
                            "images": {
                                "type": "array",
                                "items": {"type": "string", "format": "binary"},
                                "description": "Image files to upload",
                            },
                            "student_comment": {"type": "string"},
                        },
                    }
                }
            }
        }
    },
)
def medical_group_upload(
    user: VerifiedDep,
    images: list[UploadFile] = File(..., description="Image files to upload"),
    student_comment: str | None = Form(""),
) -> MedicalGroupReferenceUploadResponseSchema:
    """
    Upload medical group reference with multiple images.
    """
    if not is_student(user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only students can upload medical group references",
        )

    semester = get_current_semester()

    try:
        with transaction.atomic():
            reference = MedicalGroupReference.objects.create(
                student_id=user.pk,
                semester=semester,
                student_comment=student_comment or "",
            )

            objs: list[MedicalGroupReferenceImage] = []
            for img in images:
                ref_img = MedicalGroupReferenceImage(reference=reference)
                # assign file to model field if exists
                ref_img.image.save(img.filename, img.file, save=False)
                objs.append(ref_img)
            MedicalGroupReferenceImage.objects.bulk_create(objs)

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )

    return MedicalGroupReferenceUploadResponseSchema.model_validate(
        reference, from_attributes=True
    )

