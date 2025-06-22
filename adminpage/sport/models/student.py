from django.conf import settings
from django.core.mail import send_mail
from django.db import models
from django.core.exceptions import ValidationError
from django.db.models.signals import post_save
from django.dispatch.dispatcher import receiver
from tinymce.models import HTMLField

from sport.models import MedicalGroupHistory, Gender
from sport.utils import get_current_study_year


def validate_course(course):
    if course is None:
        pass
    if course < 1 or course > 4:
        raise ValidationError('Course is bounded by 1 and 4')


class Student(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        null=False,
        limit_choices_to={
            'groups__verbose_name': settings.STUDENT_AUTH_GROUP_VERBOSE_NAME
        },
        primary_key=True,
    )

    gender = models.IntegerField(
        choices=Gender.choices,
        default=-1
    )

    has_QR = models.BooleanField(
        default=False,
    )

    is_online = models.BooleanField(
        default=False,
    )

    course = models.PositiveSmallIntegerField(
        default=1,
        validators=[validate_course],
        null=True,
        blank=True
    )

    medical_group = models.ForeignKey(
        'MedicalGroup',
        on_delete=models.DO_NOTHING,
        default=-2,
    )

    enrollment_year = models.PositiveSmallIntegerField(
        default=get_current_study_year,
    )

    telegram = models.CharField(
        max_length=50,
        null=True,
        blank=True
    )

    student_status = models.ForeignKey(
        'StudentStatus',
        on_delete=models.DO_NOTHING,
        default=0
    )

    sport = models.ForeignKey(
        'Sport',
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    comment = HTMLField(null=True, blank=True, default='')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.__original_medical_group = self.medical_group

    def notify(self, subject, message, **kwargs):
        msg = message.format(**kwargs)
        send_mail(
            subject,
            msg,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[self.user.email],
            html_message=msg.replace("\n", "<br>"),
        )

    def save(self, *args, **kwargs):
        if self.telegram is not None and self.telegram[0] != '@':
            self.telegram = '@' + self.telegram
        if self.medical_group != self.__original_medical_group:
            MedicalGroupHistory.objects.create(student=self,
                                               medical_group=self.medical_group)

        super().save(*args, **kwargs)

    class Meta:
        db_table = "student"
        verbose_name_plural = "students"

    def full_name(self):
        return f"{self.user.first_name} {self.user.last_name}"

    def __str__(self):
        return f"{self.user.first_name} {self.user.last_name} " \
               f"({self.user.email})"


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def save_student_profile(sender, instance, **kwargs):
    if Student.objects.filter(user=instance.pk).exists():
        instance.student.save()
