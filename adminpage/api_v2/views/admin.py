from django.contrib.auth import get_user_model
from django.db import IntegrityError
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema
from rest_framework import serializers, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response

from api_v2.permissions import IsSuperUser
from api_v2.serializers.student import StudentSerializer
from sport.models import Student, Trainer

User = get_user_model()


class CreateUserRequestSerializer(serializers.Serializer):
    email = serializers.EmailField()
    username = serializers.CharField(required=False, allow_blank=True, default="")
    first_name = serializers.CharField(required=False, allow_blank=True, default="")
    last_name = serializers.CharField(required=False, allow_blank=True, default="")
    password = serializers.CharField(
        required=False, allow_blank=True, default="", write_only=True
    )

    role = serializers.ChoiceField(
        choices=["student", "trainer"], required=False, allow_null=True
    )

    is_staff = serializers.BooleanField(required=False, default=False)
    is_superuser = serializers.BooleanField(required=False, default=False)


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
    responses={status.HTTP_200_OK: StudentSerializer()},
)
@api_view(["GET"])
@permission_classes([IsSuperUser])
def get_user_by_id(request, user_id: int, **kwargs):
    user = get_object_or_404(User, pk=user_id)
    instance = _wrap_for_user_serializer(user)
    return Response(StudentSerializer(instance).data, status=status.HTTP_200_OK)


@extend_schema(
    methods=["POST"],
    tags=["For admin"],
    summary="Create new user",
    description="Create a new user (can give him any role)",
    request=CreateUserRequestSerializer,
    responses={status.HTTP_201_CREATED: StudentSerializer()},
)
@api_view(["POST"])
@permission_classes([IsSuperUser])
def create_users_batch(request, **kwargs):
    body = CreateUserRequestSerializer(data=request.data)
    body.is_valid(raise_exception=True)
    data = body.validated_data

    try:
        user = User.objects.create_user(
            email=data["email"],
            first_name=data.get("first_name", ""),
            last_name=data.get("last_name", ""),
            password=data.get("password", "") or None,
        )

        changed = False
        if data.get("is_staff", False):
            user.is_staff = True
            changed = True
        if data.get("is_superuser", False):
            user.is_superuser = True
            changed = True
        if changed:
            user.save(update_fields=["is_staff", "is_superuser"])

        role = data.get("role")
        if role == "student" and not hasattr(user, "student"):
            Student.objects.create(user=user)
        elif role == "trainer" and not hasattr(user, "trainer"):
            Trainer.objects.create(user=user)

        instance = _wrap_for_user_serializer(user)
        return Response(
            StudentSerializer(instance).data, status=status.HTTP_201_CREATED
        )

    except IntegrityError as e:
        return Response(
            {"detail": f"Integrity error: {str(e)}"},
            status=status.HTTP_400_BAD_REQUEST,
        )
