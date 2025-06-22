from datetime import timedelta

from django.db import models
from django.db.models import Q, F
from django.utils import timezone
from sport.utils import today

from . import MedicalGroup, StudentStatuses
from .course import Course
from .student import Student


def now_offset(offset=0):
    return timezone.now() + timedelta(seconds=offset)


def academic_leave_students():
    return Student.objects.filter(student_status=StudentStatuses.ACADEMIC_LEAVE)


def all_courses():
    return Course.objects.all()


class Semester(models.Model):
    name = models.CharField(max_length=50, null=False, unique=True)
    start = models.DateField(null=False, default=today)
    end = models.DateField(null=False, default=today)
    academic_leave_students = models.ManyToManyField(Student, blank=True, default=academic_leave_students,
                                                     related_name="academic_leave_semesters")
    hours = models.IntegerField(default=30)
    points_fitness_test = models.IntegerField(default=40)
    number_hours_one_week_ill = models.IntegerField(default=2)
    nullify_groups = models.ManyToManyField(MedicalGroup, blank=True)
    increase_course = models.BooleanField(default=False)
    participating_courses = models.ManyToManyField(Course, blank=False, default=all_courses)

    class Meta:
        db_table = "semester"
        verbose_name_plural = "semesters"
        constraints = [
            models.CheckConstraint(check=Q(start__lte=F('end')), name='semester_start_before_end')
        ]
        indexes = [
            models.Index(fields=("start",)),
        ]

    def __str__(self):
        return f"{self.name}"
