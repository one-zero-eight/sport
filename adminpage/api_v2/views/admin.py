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
    responses={status.HTTP_201_CREATED: UserSerializer(many=True)},
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

"""
I rewrote this method by mistake, but I feel bad deleting it.

class CreateUserRequestSerializer(serializers.Serializer):
    email = serializers.EmailField()
    username = serializers.CharField(required=False, allow_blank=True, default="")
    first_name = serializers.CharField(required=False, allow_blank=True, default="")
    last_name = serializers.CharField(required=False, allow_blank=True, default="")
    password = serializers.CharField(
        required=False, allow_blank=True, default="", write_only=True
    )
    
    # Изменено на MultipleChoiceField для выбора нескольких ролей
    roles = serializers.MultipleChoiceField(
        choices=["student", "trainer"], 
        required=False, 
        default=[]
    )
    
    is_staff = serializers.BooleanField(required=False, default=False)
    is_superuser = serializers.BooleanField(required=False, default=False)

@extend_schema(
    methods=["POST"],
    tags=["For admin"],
    summary="Create new users",
    description="Create a new users (can give him any role)",
    request=CreateUserRequestSerializer(many=True),
    responses={status.HTTP_201_CREATED: UserSerializer(many=True)},
)
@api_view(["POST"])
@permission_classes([IsSuperUser])
def create_users_batch(request, **kwargs):
    body = CreateUserRequestSerializer(many=True, data=request.data)
    body.is_valid(raise_exception=True)
    data = body.validated_data
    try:
        response = []
        for recived_user in data:

            user = User.objects.create_user(
                email=recived_user["email"],
                first_name=recived_user.get("first_name", ""),
                last_name=recived_user.get("last_name", ""),
                password=recived_user.get("password", "") or None,
            )

            changed = False
            if recived_user.get("is_staff", False):
                user.is_staff = True
                changed = True
            if recived_user.get("is_superuser", False):
                user.is_superuser = True
                changed = True
            if changed:
                user.save(update_fields=["is_staff", "is_superuser"])

            roles = recived_user.get("roles")
            if "student" in roles and not hasattr(user, "student"):
                Student.objects.create(user=user)
            if "trainer" in roles and not hasattr(user, "trainer"):
                Trainer.objects.create(user=user)

            response.append(_wrap_for_user_serializer(user))
        
        return Response(
            UserSerializer(response, many=True).data, status=status.HTTP_201_CREATED
        )

    except IntegrityError as e:
        return Response(
            {"detail": f"Integrity error: {str(e)}"},
            status=status.HTTP_400_BAD_REQUEST,
        )
"""