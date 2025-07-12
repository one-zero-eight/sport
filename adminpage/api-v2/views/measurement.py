import datetime
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response

from api.crud import get_ongoing_semester

from api.permissions import IsStudent, IsTrainer

from api.serializers import (
    MeasurementPostSerializer,
    MeasurementResultsSerializer,
    NotFoundSerializer,
    ErrorSerializer
)

from sport.models import Measurement, MeasurementSession, MeasurementResult, Student


@extend_schema(
    methods=["GET"],
    # TODO: Check
    # parameters=[MeasurementSerializer(many=True)],
    responses={
        status.HTTP_200_OK: MeasurementResultsSerializer,
    }
)
@api_view(["GET"])
def get_measurements(request, **kwargs):
    measurements = Measurement.objects.all()
    result = []
    for measurement in measurements:
        result.append({"name": measurement.name, "value_unit": measurement.value_unit})
    return Response(result)


@extend_schema(
    methods=["GET"],
    # TODO: Check
    # parameters=[MeasurementResultsSerializer],
    responses={
        status.HTTP_200_OK: MeasurementResultsSerializer,
    }
)
@api_view(["GET"])
@permission_classes([IsStudent])
def get_results(request, **kwargs):
    session = MeasurementSession.objects.filter(student=request.user.student)
    if not len(session):
        return Response([])
    else:
        session = session[0]
    results = MeasurementResult.objects.filter(session=session)
    response = {}
    if not len(results):
        return Response({"code": "There is no results"})
    for result in results:
        _result = {
            'measurement': result.measurement.name,
            'unit': result.measurement.value_unit,
            'value': result.value,
            'approved': result.session.approved,
            'date': result.session.date,
        }
        if response.get(result.session.semester.name, None) is None:
            response[result.session.semester.name] = [_result]
        else:
            response[result.session.semester.name].append(_result)
    return Response([{"semester": key, "result": response[key]} for key in response.keys()])


@extend_schema(
    methods=["POST"],
    request=MeasurementPostSerializer,
    responses={
        status.HTTP_404_NOT_FOUND: NotFoundSerializer,
        status.HTTP_400_BAD_REQUEST: ErrorSerializer,
    },
)
@api_view(["POST"])
@permission_classes([IsTrainer])
def post_student_measurement(request, **kwargs):
    approved = False
    if hasattr(request.user, 'trainer'):
        approved = True
    student = request.user.student if approved is False else Student.objects.get(user_id=request.data['student_id'])
    measurement = Measurement.objects.filter(id=request.data['measurement_id'])
    if not len(measurement):
        return Response({})
    else:
        measurement = measurement[0]
    session = MeasurementSession.objects.get_or_create(student=student, approved=approved,
                                                       date=datetime.datetime.today(),
                                                       semester=get_ongoing_semester())[0]

    result = MeasurementResult.objects.get_or_create(measurement=measurement, session=session)
    result[0].value = request.data['value']
    result[0].save()
    return Response({'result_id': result[0].id})
