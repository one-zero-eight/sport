import uuid
from typing import Tuple

from django.conf import settings
from django.core.validators import URLValidator
from django.db import models
from image_optimizer.fields import OptimizedImageField

from sport.utils import SubmissionType


def get_report_path(instance, filename):
    ext = filename.split('.')[-1]
    return f'{settings.SELF_SPORT_FOLDER}/{instance.semester.name}/' \
           f'{instance.student.pk}/{uuid.uuid4()}.{ext}'


class SelfSportReport(models.Model):
    student = models.ForeignKey(
        'Student',
        on_delete=models.CASCADE,
        null=False,
        blank=False,
    )
    semester = models.ForeignKey(
        'Semester',
        on_delete=models.CASCADE,
        null=False,
        blank=False,
    )
    image = OptimizedImageField(
        upload_to=get_report_path,
        optimized_image_resize_method='thumbnail',
        null=True,
        blank=True,
    )
    link = models.URLField(
        max_length=100,
        null=True,
        blank=True,
        validators=[URLValidator(schemes=['http', 'https'])]
    )
    # start = models.DateTimeField(
    #     null=True,
    #     blank=False,
    # )
    # end = models.DateTimeField(
    #     null=True,
    #     blank=False,
    # )
    training_type = models.ForeignKey(
        'sport.SelfSportType',
        on_delete=models.SET_NULL,
        null=True,
    )
    debt = models.BooleanField(
        null=False,
        default=False
    )

    hours = models.IntegerField(default=0)
    uploaded = models.DateTimeField(
        auto_now_add=True,
        null=False
    )
    approval = models.BooleanField(
        null=True
    )

    comment = models.TextField(max_length=1024, null=True, blank=True)
    student_comment = models.TextField(max_length=1024, null=True, blank=True, verbose_name="Student's comment")
    parsed_data = models.JSONField(verbose_name="Data from the Strava link", null=True, blank=True)

    class Meta:
        db_table = "self_sport_report"
        constraints = [
            # empty image for some reason
            # is saved as empty string instead of null
            models.CheckConstraint(
                name="link_xor_image",
                check=
                (models.Q(link__isnull=True, ) & ~models.Q(image__exact='')) |
                models.Q(image__exact='', link__isnull=False, )
            )
        ]

    def get_submission_url(self) -> Tuple[SubmissionType, str]:
        if self.link is not None:
            submission_type = SubmissionType.LINK
            submission = self.link
        elif self.image is not None:
            submission_type = SubmissionType.IMAGE
            submission = self.image.url
        else:
            raise ValueError("Invalid object was provided")
        return submission_type, submission

    def save(self, *args, **kwargs):
        # update flag and approval only when object is created via API
        if not kwargs.get('force_insert', False):
            self.hours = max(self.hours, 0)
            self.approval = self.hours > 0
        return super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.student} {self.uploaded.strftime('%Y-%m-%d %H:%M:%S')} for {self.semester}"
