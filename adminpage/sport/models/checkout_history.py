from django.db import models


class CheckoutHistory(models.Model):
    class Reason(models.TextChoices):
        STUDENT_CANCEL = "The recording was deleted by the student."
        TRAINER_CANCEL = "The recording was deleted by the coach."
        TRAINING_CANCELLED = "Cancellation of training"
        TRAINING_TIME_CHANGED = "Change training time"

    student = models.ForeignKey("Student", on_delete=models.SET_NULL, null=True)
    training = models.ForeignKey("Training", on_delete=models.SET_NULL, null=True)
    checkin_date = models.DateTimeField()
    checkout_date = models.DateTimeField(auto_now_add=True)
    checkout_reason = models.CharField(max_length=50, choices=Reason.choices)

    @classmethod
    def from_checkin(cls, checkin, reason):
        return cls.objects.create(
            student=checkin.student,
            training=checkin.training,
            checkin_date=checkin.date,
            checkout_reason=reason,
        )

    @classmethod
    def bulk_from_checkins(cls, checkins, reason):
        records = [
            cls(
                student=c.student,
                training=c.training,
                checkin_date=c.date,
                checkout_reason=reason,
            )
            for c in checkins
        ]
        return cls.objects.bulk_create(records)

    def __str__(self):
        return f"{self.student} checkout from {self.training} ({self.checkout_reason})"
