from django.db import models


class TrainingReminder(models.Model):
    training = models.ForeignKey(
        "Training",
        on_delete=models.CASCADE,
        related_name="reminders",
    )
    student = models.ForeignKey(
        "Student",
        on_delete=models.CASCADE,
        related_name="reminders",
    )
    sent_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "training_reminder"
        verbose_name = "training reminder"
        verbose_name_plural = "training reminders"
        constraints = [
            models.UniqueConstraint(
                fields=["training", "student"],
                name="unique_training_reminder_per_student",
            )
        ]

    def __str__(self):
        return f"Reminder for {self.training} → {self.student} (sent {self.sent_at})"
