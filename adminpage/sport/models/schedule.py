from django.db import models
from django.db.models import Q, F


class Schedule(models.Model):
    class Weekday(models.IntegerChoices):
        MONDAY = 0, "Monday"
        TUESDAY = 1, "Tuesday"
        WEDNESDAY = 2, "Wednesday"
        THURSDAY = 3, "Thursday"
        FRIDAY = 4, "Friday"
        SATURDAY = 5, "Saturday"
        SUNDAY = 6, "Sunday"

    group = models.ForeignKey('Group', on_delete=models.CASCADE, null=False, related_name="schedule")
    weekday = models.IntegerField(choices=Weekday.choices, null=False)
    start = models.TimeField(auto_now=False, auto_now_add=False, null=False)
    end = models.TimeField(auto_now=False, auto_now_add=False, null=False)
    training_class = models.ForeignKey("TrainingClass", on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        db_table = "schedule"
        verbose_name = "schedule timeslot"
        verbose_name_plural = "schedule timeslots"
        constraints = [
            models.CheckConstraint(check=Q(start__lt=F('end')), name='schedule_start_before_end'),
        ]

    def __str__(self):
        return f"{self.group} {self.get_weekday_display()} {self.start}-{self.end}" \
               f"{'' if self.training_class is None else f' in {self.training_class}'}"
