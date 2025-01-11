import datetime

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group as AuthGroup
from django.db.models.functions import Coalesce
from django.db.models.signals import post_save, pre_save, m2m_changed
from django.dispatch.dispatcher import receiver
from django.db.models import F, OuterRef, ExpressionWrapper, IntegerField
from datetime import datetime

from sport.models import Semester, Sport, Trainer, Group, Schedule, Student, Debt, Attendance

from api.crud import get_free_places_for_sport, SumSubquery, get_ongoing_semester

User = get_user_model()


def get_or_create_student_group():
    return AuthGroup.objects.get_or_create(
        verbose_name=settings.STUDENT_AUTH_GROUP_VERBOSE_NAME,
        defaults={
            "name": settings.STUDENT_AUTH_GROUP_NAME,
        }
    )[0]


def get_or_create_trainer_group():
    return AuthGroup.objects.get_or_create(
        verbose_name=settings.TRAINER_AUTH_GROUP_VERBOSE_NAME,
        defaults={
            "name": settings.TRAINER_AUTH_GROUP_NAME,
        }
    )[0]


@receiver(post_save, sender=Semester)
def special_groups_create(sender, instance, created, **kwargs):
    get_free_places_for_sport(1)
    if created:
        trainer_group = get_or_create_trainer_group()
        sport_dep_user, _ = User.objects.get_or_create(
            first_name="Sport",
            last_name="Department",
            email=settings.SPORT_DEPARTMENT_EMAIL,
            defaults={
                "is_active": True,
            }
        )
        sport_dep_user.groups.add(trainer_group)
        sport_dep, _ = Trainer.objects.get_or_create(user=sport_dep_user)
        kwargs = {
            'is_club': False,
            'sport': None,
            'semester': instance,
            'trainer': sport_dep
        }
        Group.objects.create(
            name=settings.SELF_TRAINING_GROUP_NAME,
            capacity=9999,
            **kwargs
        )
        Group.objects.create(
            name=settings.EXTRA_EVENTS_GROUP_NAME,
            capacity=0,
            **kwargs,
        )
        Group.objects.create(
            name=settings.MEDICAL_LEAVE_GROUP_NAME,
            capacity=0,
            **kwargs
        )
    # TODO: add logic for semester update
    # else:
    #     # if semester dates changed, recalculate all future related schedules
    #     old = Semester.objects.get(pk=instance.pk)
    #     if old.start != instance.start or old.end != instance.end:
    #         semester_schedules = Schedule.objects.filter(
    #             group__semester=instance.pk
    #         )
    #         for schedule in semester_schedules:
    #             post_save.send(
    #                 sender=Schedule,
    #                 instance=schedule,
    #                 created=False
    #             )


@receiver(pre_save, sender=Semester)
def validate_semester(sender, instance, *args, **kwargs):
    for i in Semester.objects.all():
        if i.name == instance.name:
            pass
        elif (i.start < instance.start and i.end < instance.start) or \
                (i.start > instance.end and i.end > instance.end):
            pass
        else:
            raise ValueError("Last semester has a intersection with other semester")

    if instance.pk is None:
        try:
            qs = Student.objects.filter(student_status_id=0, course__in=get_ongoing_semester().participating_courses.all())

            # TODO: Fix duplicate warning
            qs = qs.annotate(_debt=Coalesce(
                SumSubquery(Debt.objects.filter(semester_id=get_ongoing_semester().pk,
                                                student_id=OuterRef("pk")), 'debt'),
                0
            ))
            qs = qs.annotate(_ongoing_semester_hours=Coalesce(
                SumSubquery(Attendance.objects.filter(
                    training__group__semester_id=get_ongoing_semester().pk, student_id=OuterRef("pk")), 'hours'),
                0
            ))
            qs = qs.annotate(complex_hours=ExpressionWrapper(
                F('_ongoing_semester_hours') - F('_debt'), output_field=IntegerField()
            ))

            for s in qs:
                if s.complex_hours < get_ongoing_semester().hours:
                    Debt.objects.get_or_create(student_id=s.pk, semester=None, debt=get_ongoing_semester().hours - s.complex_hours)
        except:
            pass


@receiver(m2m_changed, sender=Semester.nullify_groups.through)
def nullify_medical_groups(instance, action, reverse, pk_set, **kwargs):
    students = Student.objects.filter(medical_group_id__in=pk_set).update(medical_group_id=-2)


@receiver(post_save, sender=Semester)
def increase_course(sender, instance, created, **kwargs):
    Debt.objects.filter(semester=None).update(semester=instance)
    if not created:
        return
    Student.objects.all().update(sport=None)
    if instance.increase_course is True:
        Student.objects.filter(student_status_id=0, course__lte=3).update(course=F('course') + 1)
        Student.objects.filter(student_status_id=0, course__gte=4).update(course=None, student_status_id=3)


