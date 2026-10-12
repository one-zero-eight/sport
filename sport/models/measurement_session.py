from django.db import models
from sport.utils import today


class MeasurementSession(models.Model):
    student = models.ForeignKey(
        'Student',
        on_delete=models.CASCADE,
        null=False,
        blank=False
    )
    date = models.DateField(null=False, default=today)
    semester = models.ForeignKey(
        'Semester',
        on_delete=models.CASCADE,
        null=False,
        blank=False
    )
    approved = models.BooleanField(
        default=False
    )

    def __str__(self):
        return "Session of " + str(self.student) + ".Date: " + str(self.date)
