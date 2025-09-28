from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, Permission

from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from django.db.models.signals import m2m_changed, post_save, pre_save
from django.dispatch.dispatcher import receiver
from django_auth_adfs.signals import post_authenticate

from sport.models import Student, Trainer, CustomPermission, Group as Group_model

from api.crud.crud_semester import get_ongoing_semester

from api.crud import unenroll_student, get_student_groups

User = get_user_model()


@receiver(
    m2m_changed,
    sender=User.groups.through
)
# if user is add to a group, this will create a corresponding profile
def create_student_profile(instance, action, reverse, pk_set, **kwargs):
    if not reverse:
        current_user_groups = [v.verbose_name for v in instance.groups.filter(
            verbose_name__in=[
                settings.STUDENT_AUTH_GROUP_VERBOSE_NAME,
                settings.COLLEGE_AUTH_GROUP_VERBOSE_NAME,
                settings.TRAINER_AUTH_GROUP_VERBOSE_NAME,
            ],
        ).all()]
        has_student_group = settings.STUDENT_AUTH_GROUP_VERBOSE_NAME in current_user_groups
        has_college_group = settings.COLLEGE_AUTH_GROUP_VERBOSE_NAME in current_user_groups
        has_trainer_group = settings.TRAINER_AUTH_GROUP_VERBOSE_NAME in current_user_groups

        if has_student_group or has_college_group:
            student, _ = Student.objects.get_or_create(pk=instance.pk)
            if student.is_college != has_college_group:
                student.is_college = has_college_group
                student.save()
        else:
            Student.objects.filter(pk=instance.pk).delete()

        if action == "post_add" and has_trainer_group:
            Trainer.objects.get_or_create(pk=instance.pk)


@receiver(post_save, sender=Student)
def add_group_for_student_status(instance: Student, sender, using, **kwargs):
    expected_group_name = "STUDENT_STATUS_{}".format(instance.student_status.id)
    current_groups = instance.user.groups.filter(name__startswith="STUDENT_STATUS")

    # Check if user already has the correct group
    if current_groups.filter(name=expected_group_name).exists():
        return

    # Remove old student status groups only if they exist
    if current_groups.exists():
        instance.user.groups.remove(*current_groups)

    new_group, created = Group.objects.get_or_create(name=expected_group_name,
                                            defaults={'verbose_name': "[Student status] {}".format(instance.student_status.name)})
    content_type = ContentType.objects.get_for_model(CustomPermission)
    if instance.student_status.name == "Normal":
        new_group.permissions.add(Permission.objects.get(codename='go_to_another_group', content_type=content_type))
        new_group.permissions.add(Permission.objects.get(codename='choose_sport', content_type=content_type))
        new_group.permissions.add(Permission.objects.get(codename='choose_group', content_type=content_type))
        new_group.permissions.add(Permission.objects.get(codename='see_calendar', content_type=content_type))
    elif instance.student_status.name == "Academic leave":
        new_group.permissions.add(Permission.objects.get(codename='see_calendar', content_type=content_type))

    instance.user.groups.add(new_group)


@receiver(pre_save, sender=Student)
def change_course(instance: Student, sender, using, **kwargs):
    if instance.student_status.name == "Alumnus":
        instance.course = None


@receiver(post_save, sender=Student)
def change_online_status(instance: Student, sender, using, **kwargs):
    user = User.objects.get(id=instance.user_id)
    content_type = ContentType.objects.get_for_model(CustomPermission)
    if instance.is_online is True:
        user.user_permissions.add(Permission.objects.get(codename='more_than_10_hours_of_self_sport', content_type=content_type))
    else:
        user.user_permissions.remove(Permission.objects.get(codename='more_than_10_hours_of_self_sport', content_type=content_type))


@receiver(post_save, sender=Student)
def change_status_to_academic_leave(instance: Student, sender, using, **kwargs):
    if instance.student_status.name == "Academic leave":
        get_ongoing_semester().academic_leave_students.add(instance)


@receiver(post_save, sender=Student)
def change_sport_of_student(instance: Student, sender, using, **kwargs):
    groups = get_student_groups(instance)
    if len(groups) == 0:
        return

    for group in groups:
        if instance.sport is None or group['sport_name'] != instance.sport.name:
            unenroll_student(Group_model.objects.get(id=group['id']), instance)


def update_group_verbose_names(sid_to_name_mapping: dict):
    groups = Group.objects.filter(name__in=sid_to_name_mapping.keys())
    for group in groups:
        group.verbose_name = sid_to_name_mapping[group.name]
    Group.objects.bulk_update(groups, ['verbose_name'])


@receiver(post_authenticate)
def verify_bachelor_role(user, claims, adfs_response, *args, **kwargs):
    print(user, claims)
    token_group_mapping = dict(zip(claims["groupsid"], claims["group"]))
    update_group_verbose_names(token_group_mapping)

    if settings.STUDENT_AUTH_GROUP_VERBOSE_NAME in claims["group"]:
        student_group = Group.objects.get(verbose_name=settings.STUDENT_AUTH_GROUP_VERBOSE_NAME)
        user.groups.add(student_group)
        user.save()

    if settings.COLLEGE_AUTH_GROUP_VERBOSE_NAME in claims["group"]:
        college_group = Group.objects.get(verbose_name=settings.COLLEGE_AUTH_GROUP_VERBOSE_NAME)
        user.groups.add(college_group)
        user.save()
