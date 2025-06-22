from django.db import models


class StudentStatus(models.Model):
    id = models.IntegerField(primary_key=True)
    name = models.CharField(max_length=50, null=False)
    description = models.TextField(max_length=1000, null=False)

    class Meta:
        db_table = "student_status"
        verbose_name_plural = "student statuses"

    def __str__(self):
        return self.name
