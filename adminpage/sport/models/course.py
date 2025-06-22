from django.db import models
from django.core.exceptions import ValidationError


def validate_course(course):
    if course is None:
        pass
    if course < 1 or course > 4:
        raise ValidationError('Course is bounded by 1 and 4')


class Course(models.Model):
    course = models.PositiveSmallIntegerField(primary_key=True)
    curator = models.ForeignKey('Trainer', on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return str(self.course)
