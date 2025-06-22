from django.db import models


class MeasurementResult(models.Model):
    session = models.ForeignKey(
        'MeasurementSession',
        on_delete=models.CASCADE,
        null=False,
        blank=False
    )

    measurement = models.ForeignKey(
        'Measurement',
        on_delete=models.CASCADE,
        null=False,
        blank=False
    )

    value = models.IntegerField(default=0)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['session', 'measurement'], name='session_measurement')
        ]
