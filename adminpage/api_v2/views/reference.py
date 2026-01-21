from django.db import transaction
from django.utils.timezone import make_naive
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes, \
    parser_classes
from rest_framework.parsers import MultiPartParser
from rest_framework.response import Response

from api_v2.crud import get_current_semester_crud
from api_v2.permissions import IsStudent
from api_v2.serializers import (
    ReferenceUploadSerializer,
    ReferenceUploadResponseSerializer,
    MedicalGroupReferenceUploadSerializer,
    MedicalGroupReferenceUploadResponseSerializer,
    EmptySerializer,
    ErrorSerializer,
    error_detail,
)
from sport.models import Student, MedicalGroupReference, Debt, MedicalGroupReferenceImage, Reference

class ReferenceErrors:
    TOO_MUCH_UPLOADS_PER_DAY = (
        3,
        "Only 1 reference upload per day is allowed"
    )


@extend_schema(
    methods=["POST"],
    tags=["For student"],
    summary="Upload medical certificate",
    description="Upload a medical certificate for sick leave. The system automatically calculates hours based on the duration of illness. Only one upload per day is allowed.",
    request=ReferenceUploadSerializer,
    responses={
        status.HTTP_200_OK: ReferenceUploadResponseSerializer,
        status.HTTP_400_BAD_REQUEST: ErrorSerializer,
    },
)
@api_view(["POST"])
@permission_classes([IsStudent])
@parser_classes([MultiPartParser])
def reference_upload(request, **kwargs):
    serializer = ReferenceUploadSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    image = serializer.validated_data['image']

    student = request.user  # user.pk == user.student.pk

    try:
        with transaction.atomic():
            ref = serializer.save(
                semester=get_current_semester_crud(),
                student_id=student.pk,
                hours=(serializer.validated_data['end'] - serializer.validated_data['start']).days // 7 * get_current_semester_crud().number_hours_one_week_ill
            )
            count = Reference.objects.filter(
                student_id=student.pk,
                uploaded__date=make_naive(ref.uploaded).date()
            ).count()
            assert count == 1
    except AssertionError:
        return Response(
            status=status.HTTP_400_BAD_REQUEST,
            data=error_detail(*ReferenceErrors.TOO_MUCH_UPLOADS_PER_DAY)
        )
    
    # Return informative response
    return Response({
        "message": "Medical certificate uploaded successfully",
        "reference_id": ref.id,
        "hours": ref.hours,
        "start": ref.start,
        "end": ref.end,
        "uploaded": ref.uploaded
    })

@extend_schema(
    methods=["POST"],
    tags=["For student"],
    summary="Upload medical certificate",
    description="Upload a medical certificate for sick leave. The system automatically calculates hours based on the duration of illness. Only one upload per day is allowed.",
    request=MedicalGroupReferenceUploadSerializer,
    responses={
        status.HTTP_200_OK: MedicalGroupReferenceUploadResponseSerializer,
        status.HTTP_400_BAD_REQUEST: ErrorSerializer,
    },
)
@api_view(["POST"])
@permission_classes([IsStudent])
@parser_classes([MultiPartParser])
def medical_group_upload(request, **kwargs):
    serializer = MedicalGroupReferenceUploadSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    images = serializer.validated_data['images']
    student_comment = serializer.validated_data.get('student_comment', '')
    student = request.user  # user.pk == user.student.pk

    try:
        with transaction.atomic():
            
            reference = MedicalGroupReference.objects.create(
                student_id=student.pk,
                semester=get_current_semester_crud(),
                student_comment=student_comment,
            )
            
            reference_images = [
                MedicalGroupReferenceImage(reference=reference, image=image)
                for image in images
            ]
            MedicalGroupReferenceImage.objects.bulk_create(reference_images)
    
    except Exception as e:
        return Response(
            {
                'error': str(e)
            },
            status=status.HTTP_400_BAD_REQUEST
        )

    return Response(MedicalGroupReferenceUploadResponseSerializer(reference).data)