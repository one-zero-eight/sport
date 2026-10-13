from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from api.crud import get_semester_crud
from api.serializers import NotFoundSerializer
from api.serializers.semester import SemesterSerializer


@extend_schema(
    methods=["GET"],
    parameters=[
        OpenApiParameter(name="current", type=OpenApiTypes.BOOL),
        OpenApiParameter(name="with_ft_exercises", type=OpenApiTypes.BOOL),
    ],
    description="Get semesters.",
    responses={
        status.HTTP_200_OK: SemesterSerializer(many=True),
        status.HTTP_404_NOT_FOUND: NotFoundSerializer(),
    },
)
@api_view(["GET"])
def get_semester(request, **kwargs):
    current = request.query_params.get("current", False)
    current = current == "true"

    with_ft_exercises = request.query_params.get("with_ft_exercises", False)
    with_ft_exercises = with_ft_exercises == "true"

    data = [SemesterSerializer(elem).data for elem in get_semester_crud(current, with_ft_exercises)]
    if data:
        return Response(status=status.HTTP_200_OK, data=data)
    else:
        return Response(status=status.HTTP_404_NOT_FOUND, data=NotFoundSerializer().data)
