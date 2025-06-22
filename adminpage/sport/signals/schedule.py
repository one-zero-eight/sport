from datetime import date, timedelta, datetime
from typing import Iterator

from django.conf import settings
from django.db.models.signals import post_save, pre_delete, pre_save
from django.dispatch.dispatcher import receiver
from django.forms.utils import to_current_timezone
from django.utils import timezone

from sport.models import Schedule, Training


def get_today() -> date:
    return timezone.now().date()


def get_current_monday() -> date:
    today = get_today()
    return today - timedelta(days=today.weekday())


def week_generator(start: date, end: date) -> Iterator[date]:
    """
    Generate monday's date for all weeks between start and date including first and last week

    :param start: start generating on week start belongs to
    :param end: stop generating on week end belongs to
    """
    start -= timedelta(days=start.weekday())
    end -= timedelta(days=end.weekday())
    while start <= end:
        yield start
        start += timedelta(weeks=1)


@receiver(pre_delete, sender=Schedule)
def remove_future_trainings_from_schedule(instance: Schedule, **kwargs):
    """
    Remove future trainings related to the schedule
    """
    # semester = instance.group.semester  # type: Semester
    # since date < datetime comparison cuts datetime, append time till 23:59:59
    # semester_end_datetime = datetime.combine(date=semester.end,
    #                                          time=timezone.make_aware(time(23, 59, 59))
    #                                          )
    Training.objects.filter(group=instance.group,  # trainings belong to group
                            start__gt=timezone.now(),  # end__lte=semester_end_datetime,  # are within semester
                            schedule=instance,  # and
                            ).delete()


@receiver(pre_save, sender=Training)
def notify_about_changed_time(instance: Training, **kwargs):
    if instance.pk:
        old = Training.objects.get(pk=instance.pk)
        print(old.start, instance.start, old.end, instance.end)
        if old.start != instance.start or old.end != instance.end:
            for student in instance.checked_in_students:
                student.notify(*settings.EMAIL_TEMPLATES['training_changed'],
                               student_name=student.user.first_name,
                               group_name=instance.group.to_frontend_name(),
                               previous_time=to_current_timezone(old.start).strftime('%d.%m.%Y %H:%M'),
                               new_time=to_current_timezone(instance.start).strftime('%d.%m.%Y %H:%M'))
            instance.checkins.all().delete()



@receiver(pre_delete, sender=Training)
def notify_about_removed_training(instance: Training, **kwargs):
    for student in instance.checked_in_students:
        student.notify(*settings.EMAIL_TEMPLATES['training_deleted'],
                       student_name=student.user.first_name,
                       group_name=instance.group.to_frontend_name(),
                       time=to_current_timezone(instance.start).strftime('%d.%m.%Y %H:%M'))


@receiver(post_save, sender=Schedule)
def create_trainings_current_semester(instance: Schedule, created, **kwargs):
    # if schedule was changed - then time or date changed,
    # so we recreate all future trainings
    if not created:
        remove_future_trainings_from_schedule(instance, **kwargs)

    semester = instance.group.semester
    today = get_today()
    server_timezone = timezone.localtime().tzinfo
    server_time = datetime.now(server_timezone)
    for week_start in week_generator(max(get_current_monday(), semester.start), semester.end):
        training_date = week_start + timedelta(days=instance.weekday)
        if today <= training_date <= semester.end:
            training_start = datetime.combine(
                date=training_date,
                time=instance.start,
                tzinfo=server_timezone
            )
            if server_time < training_start:
                training_end = datetime.combine(
                    date=training_date,
                    time=instance.end,
                    tzinfo=server_timezone
                )

                Training.objects.create(
                    group=instance.group,
                    schedule=instance,
                    start=training_start,
                    end=training_end,
                    training_class=instance.training_class,
                )
