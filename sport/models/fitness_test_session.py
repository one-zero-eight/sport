from django.db import models


class FitnessTestSession(models.Model):
    semester = models.ForeignKey('Semester', on_delete=models.CASCADE, null=False, blank=False)
    teacher = models.ForeignKey('Trainer', on_delete=models.SET_NULL, null=True, blank=True)
    retake = models.BooleanField(default=False, null=False)
    date = models.DateTimeField(null=False)

    def __str__(self):
        return f"{self.semester}{' retake' if self.retake else ''}"
