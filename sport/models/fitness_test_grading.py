from django.db import models

from sport.models import Gender
from sport.models.enums import GenderInFTGrading


class FitnessTestGrading(models.Model):
    exercise = models.ForeignKey(
        'FitnessTestExercise',
        on_delete=models.CASCADE,
        null=False,
        blank=False,
    )

    gender = models.IntegerField(
        choices=GenderInFTGrading.choices,
    )

    score = models.IntegerField()

    start_range = models.IntegerField()
    end_range = models.IntegerField()
