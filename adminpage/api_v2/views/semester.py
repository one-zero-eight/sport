from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema, OpenApiParameter
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from api_v2.crud import get_semesters_crud
from api_v2.crud import get_semester_by_id_crud
from api_v2.crud import get_current_semester_crud
from api_v2.serializers import NotFoundSerializer
from api_v2.serializers.semester import SemesterSerializer


@extend_schema(
    methods=["GET"],
    tags=["For any user"],
    summary="Get semesters information",
    description="Retrieve all semesters information.",
    responses={
        status.HTTP_200_OK: SemesterSerializer(many=True),
        status.HTTP_404_NOT_FOUND: NotFoundSerializer(),
    }
)
@api_view(['GET'])
def get_semesters(request, **kwargs):
    data = [SemesterSerializer(elem).data for elem in get_semesters_crud()]
    if len(data):
        return Response(status=status.HTTP_200_OK, data=data)
    else:
        return Response(status=status.HTTP_404_NOT_FOUND, data=NotFoundSerializer().data)
    
    
@extend_schema(
    methods=["GET"],
    tags=["For any user"],
    summary="Get semester information via id",
    description="",
    responses={
        status.HTTP_200_OK: SemesterSerializer(many=True),
        status.HTTP_404_NOT_FOUND: NotFoundSerializer(),
    }
)
@api_view(['GET'])
def get_semester_by_id(request, semester_id, **kwargs):
    semester = get_semester_by_id_crud(semester_id)
    if semester:
        data = SemesterSerializer(semester).data
        return Response(status=status.HTTP_200_OK, data=data)
    else:
        return Response(status=status.HTTP_404_NOT_FOUND, data=NotFoundSerializer().data)


@extend_schema(
    methods=["GET"],
    tags=["For any user"],
    summary="Get current semester information",
    description="",
    responses={
        status.HTTP_200_OK: SemesterSerializer(many=True),
        status.HTTP_404_NOT_FOUND: NotFoundSerializer(),
    }
)
@api_view(['GET'])
def get_current_semester(request, **kwargs):
    semester = get_current_semester_crud()
    if semester:
        data = SemesterSerializer(semester).data
        return Response(status=status.HTTP_200_OK, data=data)
    else:
        return Response(status=status.HTTP_404_NOT_FOUND, data=NotFoundSerializer().data)