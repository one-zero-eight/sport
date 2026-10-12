from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch.dispatcher import receiver

from sport.models import Group, SelfSportReport
from sport.signals.utils import create_attendance_record
from sport.utils import format_submission_html


@receiver(post_save, sender=SelfSportReport)
def update_hours_for_self_sport(
        sender,
        instance: SelfSportReport,
        created,
        **kwargs
):
    if created:
        return

    group = Group.objects.get(
        semester=instance.semester,
        name=settings.SELF_TRAINING_GROUP_NAME
    )
    training_custom_name = None
    if instance.training_type is not None:
        training_custom_name = f'[Self] {instance.training_type.name}'

    if not hasattr(instance, 'attendance'):
        instance.attendance = create_attendance_record(
            group=group,
            upload_date=instance.uploaded.date(),
            student=instance.student,
            hours=instance.hours,
            training_name=training_custom_name,
            cause_report=instance,
        )
    else:
        instance.attendance.hours = instance.hours
        instance.attendance.save()

    if instance.hours > 0:
        instance.student.notify(
            *settings.EMAIL_TEMPLATES['self_sport_success'],
            training_type=instance.training_type.name,
            date=instance.uploaded.date(),
            hours=instance.hours,
            submission=format_submission_html(
                *instance.get_submission_url()
            )
        )
    else:
        instance.attendance.delete()
        instance.student.notify(
            *settings.EMAIL_TEMPLATES['self_sport_reject'],
            training_type=instance.training_type.name,
            date=instance.uploaded.date(),
            comment=instance.comment,
            submission=format_submission_html(
                *instance.get_submission_url()
            )
        )
