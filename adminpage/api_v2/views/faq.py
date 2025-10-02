from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from api_v2.crud.crud_faq import get_faq_as_dict
from api_v2.serializers.faq import FAQDictSerializer


@extend_schema(
    methods=["GET"],
    tags=["FAQ"],
    summary="Get FAQ as dictionary",
    description="Retrieve all FAQ entries as a dictionary where questions are keys and answers are values.",
    responses={
        status.HTTP_200_OK: FAQDictSerializer(),
    }
)
@api_view(["GET"])
def get_faq_dict(request, **kwargs):
    """
    Get FAQ as dictionary with question: answer format
    """
    faq_dict = get_faq_as_dict()
    serializer = FAQDictSerializer(faq_dict)
    return Response(serializer.data) 