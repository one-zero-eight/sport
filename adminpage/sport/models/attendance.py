from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q


def validate_hours(hours):
    if hours < 0:
        raise ValidationError('Only positive values are allowed')


class Attendance(models.Model):
    training = models.ForeignKey('Training', on_delete=models.PROTECT, null=True)
    student = models.ForeignKey(
        "Student",
        limit_choices_to=~Q(medical_group__name='Medical checkup not passed'),
        on_delete=models.CASCADE,
        db_index=True
    )
    hours = models.IntegerField(default=1, validators=[validate_hours])

    # TODO: maybe PROTECT is useful here
    cause_report = models.OneToOneField('SelfSportReport', null=True, blank=True, on_delete=models.CASCADE, related_name='attendance')
    cause_reference = models.OneToOneField('Reference', null=True, blank=True, on_delete=models.CASCADE, related_name='attendance')

    class Meta:
        db_table = "attendance"
        verbose_name_plural = "attendance"
        constraints = [
            models.UniqueConstraint(fields=["training", "student"], name="unique_attendance"),
            models.CheckConstraint(check=Q(hours__gte=0), name='positive_hours')
        ]

    def __str__(self):
        return f"{self.student} -> {self.training}, {self.hours} hours"
