import datetime

from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema, OpenApiParameter
from rest_framework import status

from api.permissions import IsStaff

from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response

from sport.models import Attendance


@extend_schema(
    methods=["GET"],
    parameters=[
        OpenApiParameter(name='sport_id', type=OpenApiTypes.INT),
        OpenApiParameter(name='medical_group_id', type=OpenApiTypes.INT),
    ],
    responses={
        status.HTTP_200_OK: dict[str, int],
    }
)
@api_view(["GET"])
@permission_classes([IsStaff])
def attendance_analytics(request, **kwargs):
    sport_id, medical_group_id = request.GET.get("sport_id"), request.GET.get("medical_group_id")
    time_period = datetime.datetime.now() - datetime.timedelta(days=30)
    query = Attendance.objects.filter(training__start__gt=time_period)
    if sport_id:
        query = query.filter(training__group__sport__id=sport_id)
    if medical_group_id:
        query = query.filter(student__medical_group__id=medical_group_id)

    result = {}
    query = sorted(query, key=lambda x: x.training.start)
    for obj in query:
        time_key = obj.training.start.strftime("%Y-%m-%d")
        if time_key not in result.keys():
            result.update({time_key: 1})
        else:
            result[time_key] += 1
    return Response(result)
