import uuid

from django.conf import settings
from django.db import models


def get_reference_path(instance, filename):
    ext = filename.split('.')[-1]
    return f'{settings.MEDICAL_GROUP_REFERENCE_FOLDER}/' \
           f'{instance.reference.student.pk}/{uuid.uuid4()}.{ext}'


class MedicalGroupReference(models.Model):
    student = models.ForeignKey(
        "Student",
        on_delete=models.CASCADE,
    )

    resolved = models.BooleanField(null=True)

    semester = models.ForeignKey(
        "Semester",
        on_delete=models.CASCADE,
    )

    comment = models.TextField(max_length=1024, null=True, blank=True)
    uploaded = models.DateTimeField(
        auto_now_add=True,
        null=False
    )
    student_comment = models.TextField(max_length=1024, null=True, blank=True, verbose_name="Student's comment")
    
    def __str__(self):
        return f"{self.student} {self.uploaded.strftime('%Y-%m-%d %H:%M:%S')} for {self.semester}"

    class Meta:
        db_table = "medical_group_reference"


class MedicalGroupReferenceImage(models.Model):
    reference = models.ForeignKey(
        "MedicalGroupReference",
        verbose_name="medical reference",
        related_name="images",
        on_delete=models.CASCADE,
    )

    image = models.ImageField(
        upload_to=get_reference_path,
    )

    def __str__(self) -> str:
        return f"{self.reference} image {self.pk}"

    class Meta:
        db_table = "medical_group_reference_image"
        verbose_name = "medical group reference image"
        verbose_name_plural = "medical group reference images"
