from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from drf_spectacular.utils import extend_schema

from api.serializers import MedicalGroupsSerializer, NotFoundSerializer
from api.crud import get_medical_groups


@extend_schema(
    methods=["GET"],
    responses={
        status.HTTP_200_OK: MedicalGroupsSerializer,
        status.HTTP_404_NOT_FOUND: NotFoundSerializer,
    }
)
@api_view(["GET"])
def medical_groups_view(request, **kwargs):
    serializer = MedicalGroupsSerializer({'medical_groups': get_medical_groups()})
    return Response(serializer.data)
