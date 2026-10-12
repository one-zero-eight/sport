from django.db import models


class FitnessTestExercise(models.Model):
    exercise_name = models.CharField(
        max_length=50,
        null=False,
        blank=False
    )

    semester = models.ForeignKey(
        'Semester',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )

    value_unit = models.CharField(
        max_length=1000,
        null=True,
        blank=True
    )

    threshold = models.IntegerField(
        default=0,
        null=False,
        blank=False,
    )

    select = models.CharField(
        max_length=1000,
        null=True,
        blank=True
    )

    def __str__(self):
        return f"[{self.semester}] {self.exercise_name}"
