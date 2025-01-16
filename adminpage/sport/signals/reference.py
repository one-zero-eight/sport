from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch.dispatcher import receiver

from sport.models import Reference, Group, MedicalGroupReference
from sport.signals.utils import create_attendance_record
from sport.utils import format_submission_html


@receiver(post_save, sender=Reference)
def update_hours_for_reference(sender, instance: Reference, created, **kwargs):
    if created:
        return

    # get_or_create returns (object: Model, created: bool)
    group = Group.objects.get(
        semester=instance.semester,
        name=settings.MEDICAL_LEAVE_GROUP_NAME
    )

    if not hasattr(instance, 'attendance'):
        instance.attendance = create_attendance_record(
            group=group,
            upload_date=instance.uploaded.date(),
            student=instance.student,
            hours=instance.hours,
            cause_reference=instance,
        )
    else:
        instance.attendance.hours = instance.hours
        instance.attendance.save()

    if instance.hours > 0:
        instance.student.notify(
            *settings.EMAIL_TEMPLATES['medical_leave_success'],
            date=instance.uploaded.date(),
            hours=instance.hours,
            submission=format_submission_html(
                *instance.get_submission_url()
            ),
        )
    else:
        instance.student.notify(
            *settings.EMAIL_TEMPLATES['medical_leave_reject'],
            date=instance.uploaded.date(),
            comment=instance.comment,
            submission=format_submission_html(
                *instance.get_submission_url()
            ),
        )


@receiver(post_save, sender=MedicalGroupReference)
def medical_group_updated(
        sender,
        instance: MedicalGroupReference,
        created,
        **kwargs
):
    if created or instance.resolved is None:
        return

    if instance.resolved:
        instance.student.notify(
            *settings.EMAIL_TEMPLATES['medical_group_success'],
            semester=instance.semester,
            medical_group=instance.student.medical_group.name,
            submission=format_submission_html(
                *instance.get_submission_url()
            ),
        )
    else:
        instance.student.notify(
            *settings.EMAIL_TEMPLATES['medical_group_reject'],
            semester=instance.semester,
            comment=instance.comment,
            submission=format_submission_html(
                *instance.get_submission_url()
            ),
        )
