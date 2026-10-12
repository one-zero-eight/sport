from django.db import models


class MedicalGroup(models.Model):
    id = models.IntegerField(primary_key=True)
    name = models.CharField(max_length=50, null=False)
    description = models.TextField(max_length=1000, null=False)

    class Meta:
        db_table = "medical_group"
        verbose_name_plural = "medical groups"

    def __str__(self):
        return self.name
