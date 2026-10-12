from django.conf import settings
from django.db import models


class Trainer(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        null=False,
        primary_key=True,
    )

    class Meta:
        db_table = "trainer"
        verbose_name = "teacher"
        verbose_name_plural = "teachers"

    def __str__(self):
        return f"{self.user.first_name} {self.user.last_name}"
