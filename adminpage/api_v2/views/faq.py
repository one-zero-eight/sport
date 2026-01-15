from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response

from api_v2.crud.crud_faq import get_faq_grouped_dict
from api_v2.serializers.faq import FAQDictSerializer
from api_v2.permissions import IsStudent, IsStaff, IsTrainer


@extend_schema(
    methods=["GET"],
    tags=["For any user"],
    summary="Get FAQ grouped by category",
    description="Retrieve all FAQ entries grouped by category: {category: {question: answer}}.",
    responses={status.HTTP_200_OK: FAQDictSerializer()},
)
@api_view(["GET"])
@permission_classes([IsStudent | IsStaff | IsTrainer])
def get_faq_dict(request, **kwargs):
    faq_grouped = get_faq_grouped_dict()
    serializer = FAQDictSerializer(instance=faq_grouped)
    return Response(serializer.data, status=status.HTTP_200_OK)

