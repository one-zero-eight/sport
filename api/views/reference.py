from django.db import transaction
from django.utils.timezone import make_naive
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes, \
    parser_classes
from rest_framework.parsers import MultiPartParser
from rest_framework.response import Response

from api.crud import get_ongoing_semester
from api.permissions import IsStudent
from api.serializers import (
    ReferenceUploadSerializer,
    EmptySerializer,
    ErrorSerializer,
    error_detail,
)
from sport.models import Reference


class ReferenceErrors:
    TOO_MUCH_UPLOADS_PER_DAY = (
        3,
        "Only 1 reference upload per day is allowed"
    )


@extend_schema(
    methods=["POST"],
    request=ReferenceUploadSerializer,
    responses={
        status.HTTP_200_OK: EmptySerializer,
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
                semester=get_ongoing_semester(),
                student_id=student.pk,
                hours=(serializer.validated_data['end'] - serializer.validated_data['start']).days // 7 * get_ongoing_semester().number_hours_one_week_ill
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
    return Response({})
