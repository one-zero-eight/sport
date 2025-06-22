import uuid
from typing import Tuple

from django.db import models
from django.conf import settings
from django.utils import timezone
from smartfields import fields
from smartfields.dependencies import FileDependency
from smartfields.processors import ImageProcessor
import datetime

from sport.utils import SubmissionType


def today() -> datetime.date:
    return timezone.now().date()


def get_reference_path(instance, filename):
    ext = filename.split('.')[-1]
    return f'{settings.MEDICAL_REFERENCE_FOLDER}/{instance.semester.name}/' \
           f'{instance.student.pk}/{uuid.uuid4()}.{ext}'


class Reference(models.Model):
    student = models.ForeignKey(
        'Student',
        on_delete=models.CASCADE,
        null=False,
    )
    semester = models.ForeignKey(
        'Semester',
        on_delete=models.CASCADE,
        null=False,
    )
    image = fields.ImageField(dependencies=[
        FileDependency(processor=ImageProcessor(
            format='JPEG', scale={'max_width': 2000, 'max_height': 2000}))],
        upload_to=get_reference_path
    )

    start = models.DateField(null=False, default=today)
    end = models.DateField(null=False, default=today)
    hours = models.IntegerField(default=0)
    uploaded = models.DateTimeField(auto_now_add=True, null=False)
    approval = models.BooleanField(null=True)
    comment = models.TextField(max_length=1024, null=True, blank=True)
    student_comment = models.TextField(max_length=1024, null=True, blank=True)

    class Meta:
        db_table = "reference"
        verbose_name_plural = "medical references"

    def get_submission_url(self) -> Tuple[SubmissionType, str]:
        return SubmissionType.IMAGE, self.image.url

    def save(self, *args, **kwargs):
        # update flag and approval only when object is created via API
        if not kwargs.get('force_insert', False):
            self.hours = max(self.hours, 0)
            self.approval = self.hours > 0
        return super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.student} {self.uploaded.date()} for {self.semester}"
