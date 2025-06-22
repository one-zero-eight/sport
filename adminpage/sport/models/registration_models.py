from django.db import models

class Student(models.Model):
    email = models.EmailField(unique=True)
    full_name = models.CharField(max_length=255)

class SportSection(models.Model):
    title = models.CharField(max_length=100)
    max_participants = models.PositiveIntegerField()
    start_time = models.TimeField()
    end_time = models.TimeField()

class Registration(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    section = models.ForeignKey(SportSection, on_delete=models.CASCADE)
    registered_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('student', 'section')
