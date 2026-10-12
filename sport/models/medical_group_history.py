from django.db import models


class MedicalGroupHistory(models.Model):
    student = models.ForeignKey("Student", on_delete=models.CASCADE)
    medical_group = models.ForeignKey('MedicalGroup', on_delete=models.DO_NOTHING)
    medical_group_reference = models.ForeignKey('MedicalGroupReference', null=True, blank=True, on_delete=models.SET_NULL)
    changed = models.DateTimeField(
        auto_now_add=True,
        null=False
    )

    class Meta:
        db_table = "medical_group_history"
        verbose_name_plural = "medical groups history"
