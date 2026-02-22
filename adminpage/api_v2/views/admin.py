from django.contrib.auth import get_user_model
from django.db import IntegrityError
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema, inline_serializer
from rest_framework import serializers, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response

from api_v2.permissions import IsSuperUser
from api_v2.serializers.student import UserSerializer
from sport.models import Student, Trainer

User = get_user_model()

def _wrap_for_user_serializer(user):
    if hasattr(user, "student"):
        return user.student

    class UserWrapper:
        def __init__(self, u):
            self.user = u

    return UserWrapper(user)


@extend_schema(
    methods=["GET"],
    tags=["For admin"],
    summary="Get user by id",
    description="Get info of user by id",
    responses={status.HTTP_200_OK: UserSerializer()},
)
@api_view(["GET"])
@permission_classes([IsSuperUser])
def get_user_by_id(request, user_id: int, **kwargs):
    user = get_object_or_404(User, pk=user_id)
    instance = _wrap_for_user_serializer(user)
    return Response(UserSerializer(instance).data, status=status.HTTP_200_OK)



@extend_schema(
    methods=["POST"],
    tags=["For admin"],
    summary="Get many users by ids",
    description="Get many users by ids",
    request=serializers.ListSerializer(child=serializers.IntegerField()),
    responses={status.HTTP_200_OK: UserSerializer(many=True)},
)
@api_view(["POST"])
@permission_classes([IsSuperUser])
def get_users_batch(request, **kwargs):
    user_ids = request.data
    if not isinstance(user_ids, list):
        return Response(
            {"error": "Expected a JSON array of user IDs"},
            status=status.HTTP_400_BAD_REQUEST
        )
    try:
        users = User.objects.filter(id__in=list(set(user_ids)))
        for user in users:
            user = _wrap_for_user_serializer(user)
        return Response(UserSerializer(users, many=True).data)
    except IntegrityError as e:
        return Response(
            {"detail": f"Integrity error: {str(e)}"},
            status=status.HTTP_400_BAD_REQUEST,
        )
