from django.db import models


class TrainingCheckIn(models.Model):
    date = models.DateTimeField(auto_now_add=True)
    student = models.ForeignKey("Student", on_delete=models.CASCADE, related_name='checkins')
    training = models.ForeignKey("Training", on_delete=models.CASCADE, related_name='checkins')
    attendance = models.OneToOneField('Attendance',
                                      null=True, blank=True, on_delete=models.SET_NULL, related_name='checkin')

    def __str__(self):
        return f"{self.student} at {self.training}"

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['student', 'training'], name='student_training_checkin')
        ]
