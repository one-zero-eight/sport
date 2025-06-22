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


def get_current_group_mapping():
    group_mapping = {}
    user_groups = Group.objects.filter(
        verbose_name__in=[
            settings.STUDENT_AUTH_GROUP_VERBOSE_NAME,
            settings.TRAINER_AUTH_GROUP_VERBOSE_NAME,
        ],
    ).all()

    for group in user_groups:
        group_mapping.update({group.verbose_name: group.pk})

    return group_mapping


@receiver(
    m2m_changed,
    sender=User.groups.through
)
# if user is add to a group, this will create a corresponding profile
def create_student_profile(instance, action, reverse, pk_set, **kwargs):
    if not reverse:
        group_mapping = get_current_group_mapping()
        if group_mapping.get(
                settings.STUDENT_AUTH_GROUP_VERBOSE_NAME,
                None
        ) in pk_set:
            if action == "post_add":
                Student.objects.get_or_create(pk=instance.pk)
            if action == "pre_remove":
                Student.objects.filter(pk=instance.pk).delete()

        if group_mapping.get(
                settings.TRAINER_AUTH_GROUP_VERBOSE_NAME,
                None
        ) in pk_set:
            if action == "post_add":
                Trainer.objects.get_or_create(pk=instance.pk)


@receiver(post_save, sender=Student)
def add_group_for_student_status(instance: Student, sender, using, **kwargs):
    instance.user.groups.remove(*instance.user.groups.filter(name__startswith="STUDENT_STATUS"))
    new_group, created = Group.objects.get_or_create(name="STUDENT_STATUS_{}".format(instance.student_status.id),
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
    """
    Remove student account from non-bachelor students
    """
    token_group_mapping = dict(zip(claims["groupsid"], claims["group"]))
    update_group_verbose_names(token_group_mapping)

    if settings.STUDENT_AUTH_GROUP_VERBOSE_NAME in claims["group"] and \
            user.role is not None:
        is_active_student = user.role.startswith(
            settings.BACHELOR_GROUPS_PREFIX
        )
        # To unban mistakenly banned people
        user.is_active = True
#         if not is_active_student:
#             group_mapping = get_current_group_mapping()
#             student_group = group_mapping.get(
#                 settings.STUDENT_AUTH_GROUP_VERBOSE_NAME,
#                 None
#             )
#             user.groups.remove(student_group)
        user.save()
