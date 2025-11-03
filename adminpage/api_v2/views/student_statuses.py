from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from api_v2.crud.crud_student_statuses import get_student_statuses as get_student_statuses_crud
from api_v2.serializers.student_statuses import StudentStatusSerializer
from api_v2.serializers import NotFoundSerializer


@extend_schema(
    methods=["GET"],
    tags=["For any user"],
    summary="Get all student statuses",
    description="Retrieve a list of all possible student statuses.",
    responses={
        status.HTTP_200_OK: StudentStatusSerializer(many=True),
        status.HTTP_404_NOT_FOUND: NotFoundSerializer(),
    }
)
@api_view(['GET'])
def get_student_statuses(request, **kwargs):
    statuses = get_student_statuses_crud()
    data = [StudentStatusSerializer(s).data for s in statuses]

    if data:
        return Response(status=status.HTTP_200_OK, data=data)
    else:
        return Response(status=status.HTTP_404_NOT_FOUND, data=NotFoundSerializer().data)
