from django.db import models


class Debt(models.Model):
    student = models.ForeignKey("Student", on_delete=models.CASCADE)
    semester = models.ForeignKey("Semester", on_delete=models.CASCADE, null=True, blank=True)
    debt = models.IntegerField(default=0)

    def save(self, *args, **kwargs):
        self.debt = abs(self.debt)

        return super().save(*args, **kwargs)

    class Meta:
        db_table = "debt"
        verbose_name_plural = "debts"
