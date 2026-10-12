from django.db import models


class FitnessTestResult(models.Model):
    student = models.ForeignKey(
        "Student",
        on_delete=models.CASCADE,
        null=False,
        blank=False,
    )

    exercise = models.ForeignKey(
        'FitnessTestExercise',
        on_delete=models.CASCADE,
        null=False,
        blank=False,
    )

    session = models.ForeignKey(
        'FitnessTestSession',
        on_delete=models.CASCADE,
        null=False,
        blank=False
    )

    value = models.IntegerField(
        null=True,
        blank=True
    )

    # TODO: think about constarints
    # class Meta:
    #     constraints = [
    #         models.UniqueConstraint(fields=['student', 'exercise'], name='student_exercise')
    #     ]
