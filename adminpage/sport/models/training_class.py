from django.db import models


class TrainingClass(models.Model):
    name = models.CharField(max_length=20, null=False)

    class Meta:
        db_table = "training_class"
        verbose_name = "training class"
        verbose_name_plural = "training classes"

    def __str__(self):
        return f"{self.name}"
