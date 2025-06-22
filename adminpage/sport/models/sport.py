from django.db import models
from tinymce.models import HTMLField


class Sport(models.Model):
    name = models.CharField(max_length=50, null=False)
    description = HTMLField(blank=True)
    special = models.BooleanField(default=False, null=False, verbose_name="Technical")
    visible = models.BooleanField(default=True, null=False)

    class Meta:
        db_table = "sport"
        verbose_name = "sport type"
        verbose_name_plural = "sport types"
        indexes = [
            models.Index(fields=("name",)),
        ]

    def __str__(self):
        return f"{self.name}"
