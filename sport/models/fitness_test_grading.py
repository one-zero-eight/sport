from django.db import models

from sport.models.enums import GenderInFTGrading


class FitnessTestGrading(models.Model):
    exercise = models.ForeignKey(
        "FitnessTestExercise",
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

    def __str__(self):
        return f"{self.exercise} [{self.start_range}, {self.end_range}) → {self.score}"
