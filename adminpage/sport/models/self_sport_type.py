from django.db import models


class SelfSportType(models.Model):
    name = models.CharField(
        max_length=50,
        null=False,
        unique=True,
    )

    application_rule = models.TextField()

    is_active = models.BooleanField(
        default=True
    )

    def __repr__(self):
        return self.name

    def __str__(self):
        return self.__repr__()

    class Meta:
        db_table = "self_sport_group"
