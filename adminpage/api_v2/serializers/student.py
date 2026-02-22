from rest_framework import serializers
from api_v2.crud.crud_groups import get_trainer_groups


class StudentInfoSerializer(serializers.Serializer):
    medical_group = serializers.CharField(allow_null=True)
    student_status = serializers.CharField(allow_null=True, required=False)


class GroupSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    name = serializers.CharField()


class TrainerInfoSerializer(serializers.Serializer):
    groups = serializers.ListField(child=GroupSerializer())


class UserSerializer(serializers.Serializer):
    user_id = serializers.IntegerField()
    email = serializers.CharField()
    first_name = serializers.CharField()
    last_name = serializers.CharField()
    user_statuses = serializers.ListField(child=serializers.CharField())
    student_info = StudentInfoSerializer(allow_null=True, required=False)
    trainer_info = TrainerInfoSerializer(allow_null=True, required=False)


    def to_representation(self, obj):
        user = obj.user if hasattr(obj, "user") else obj

        data = {
            "user_id": int(user.id),
            "email": user.email,
            "first_name": user.first_name,
            "last_name": user.last_name,
        }

        roles = []
        if getattr(user, "is_superuser", False):
            roles.append("superuser")
        if getattr(user, "is_staff", False):
            roles.append("staff")
        if hasattr(user, "trainer"):
            roles.append("trainer")
        if hasattr(user, "student"):
            roles.append("student")
        if not roles:
            roles.append("user")
        data["user_statuses"] = roles

        if hasattr(user, "student") and "student" in roles:
            s = user.student
            student_block = {
                "medical_group": s.medical_group.name if getattr(s, "medical_group", None) else None,
            }
            if getattr(s, "student_status", None):
                student_block["student_status"] = s.student_status.name
            if any(v is not None for v in student_block.values()):
                data["student_info"] = student_block

        if hasattr(user, "trainer") and "trainer" in roles:
            data["trainer_info"] = {
                "groups": get_trainer_groups(user.trainer),
            }

        return data
