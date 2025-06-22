from __future__ import annotations
from typing import TYPE_CHECKING
from django.db import models
from django.db.models import Q, F, QuerySet
from django.forms.utils import to_current_timezone
from django.conf import settings

from sport.utils import notify_students

if TYPE_CHECKING:
    from sport.models import Student


class Training(models.Model):
    group = models.ForeignKey("Group", on_delete=models.CASCADE)
    schedule = models.ForeignKey("Schedule", on_delete=models.SET_NULL, null=True, blank=True)
    start = models.DateTimeField(null=False)
    end = models.DateTimeField(null=False)
    training_class = models.ForeignKey("TrainingClass", on_delete=models.SET_NULL, null=True, blank=True)
    custom_name = models.CharField(max_length=100, null=True, blank=True)

    class Meta:
        db_table = "training"
        verbose_name_plural = "trainings"
        constraints = [
            models.CheckConstraint(check=Q(start__lt=F('end')), name='training_start_before_end')
        ]
        indexes = [
            models.Index(fields=("group", "start")),
        ]

    def __str__(self):
        return f"{self.group} at {to_current_timezone(self.start).date()} " \
               f"{to_current_timezone(self.start).time().strftime('%H:%M')}-" \
               f"{to_current_timezone(self.end).time().strftime('%H:%M')}"

    @property
    def checked_in_students(self) -> QuerySet[Student]:
        from sport.models import Student
        return Student.objects.filter(checkins__in=self.checkins.all()).distinct()

    @property
    def academic_duration(self) -> float:
        if not self.group.accredited:
            return 0

        secs = (self.end - self.start).total_seconds()
        duration_sec = 2700
        duration_for_1h = duration_sec * settings.ACADEMIC_DURATION_PERCENTAGE
        return min(
            (secs + duration_for_1h) // duration_sec,
            settings.ACADEMIC_DURATION_MAX
        )
