from rest_framework import serializers

from sport.models import MedicalGroupReference, MedicalGroupReferenceImage, Reference
from django.core.validators import FileExtensionValidator

class ReferenceUploadSerializer(serializers.ModelSerializer[Reference]):
    image = serializers.ImageField(allow_empty_file=False)
    start = serializers.DateField(allow_null=False)
    end = serializers.DateField(allow_null=False)
    student_comment = serializers.CharField(max_length=1024, allow_blank=True, allow_null=True, required=False)

    class Meta:
        model = Reference
        fields = ['image', 'start', 'end', 'student_comment']


class ReferenceUploadResponseSerializer(serializers.ModelSerializer[Reference]):
    message = serializers.CharField(default="Medical certificate uploaded successfully")

    class Meta:
        model = Reference
        fields = ("id", "student_id", "semester", "hours", "start", "end", "uploaded", "message")



class MedicalGroupReferenceUploadSerializer(serializers.Serializer):
    images = serializers.ListField(
        child=serializers.ImageField(
            max_length=100000,
            allow_empty_file=False,
            validators=[FileExtensionValidator(allowed_extensions=['jpg', 'jpeg', 'png', 'pdf'])]
        ),
        write_only=True,
        min_length=1,
        max_length=10,
        help_text="List of medical reference images (allow formats: jpg, jpeg, png, pdf)"
    )
    student_comment = serializers.CharField(
        required=False,
        allow_blank=True,
        max_length=1000,
    )

class MedicalGroupReferenceUploadResponseSerializer(serializers.ModelSerializer):
    class Meta:
        model = MedicalGroupReference
        fields = ('id', 'student_id', 'semester', 'uploaded')


