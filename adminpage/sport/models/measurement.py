from django.db import models


class Measurement(models.Model):
    name = models.CharField(
        max_length=1000,
        null=True,
        blank=True
    )

    value_unit = models.CharField(
        max_length=1000,
        null=True,
        blank=True
    )

    def __str__(self):
        return self.name
