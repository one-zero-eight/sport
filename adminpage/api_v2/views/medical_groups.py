from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from api_v2.crud import get_medical_groups
from api_v2.serializers import MedicalGroupsSerializer


@extend_schema(
    methods=["GET"],
    tags=["Medical"],
    summary="Get medical groups",
    description="Retrieve list of all medical groups that determine student's physical activity allowances.",
    responses={
        status.HTTP_200_OK: MedicalGroupsSerializer,
    }
)
@api_view(["GET"])
def medical_groups_view(request, **kwargs):
    serializer = MedicalGroupsSerializer({'medical_groups': get_medical_groups()})
    return Response(serializer.data)
