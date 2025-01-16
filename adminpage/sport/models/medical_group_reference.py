import uuid
from typing import Tuple

from django.conf import settings
from django.db import models

from sport.utils import SubmissionType


def get_reference_path(instance, filename):
    ext = filename.split('.')[-1]
    return f'{settings.MEDICAL_GROUP_REFERENCE_FOLDER}/' \
           f'{instance.student.pk}/{uuid.uuid4()}.{ext}'


class MedicalGroupReference(models.Model):
    student = models.ForeignKey(
        "Student",
        on_delete=models.CASCADE,
    )

    image = models.ImageField(
        upload_to=get_reference_path,
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
    # def __str__(self):
    #     return f'{self.student} - {self.semester}'

    def get_submission_url(self) -> Tuple[SubmissionType, str]:
        return SubmissionType.IMAGE, self.image.url
    
    def __str__(self):
        return f"{self.student} {self.uploaded.strftime('%Y-%m-%d %H:%M:%S')} for {self.semester}"

    class Meta:
        db_table = "medical_group_reference"
