from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response


from api.crud import get_training_class
from api.permissions import IsStudent, IsTrainer, IsSuperUser
from api.serializers import TrainingClassSerializer, NotFoundSerializer



@extend_schema(
    methods=["GET"],
    responses={
        status.HTTP_200_OK: TrainingClassSerializer,
        status.HTTP_404_NOT_FOUND: NotFoundSerializer,
    }
)
@api_view(["GET"])
@permission_classes([IsStudent | IsTrainer | IsSuperUser])
def get_training_class_view(request, **kwargs):
    rooms = get_training_class()
    serializer = TrainingClassSerializer(rooms, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)
