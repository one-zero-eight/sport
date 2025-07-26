from typing import Optional

from django.conf import settings
from django.db import connection
from django.db.models import F
from django.db.models import Q
from django.db.models import Count, Sum, IntegerField

import api.crud
from api.crud.utils import dictfetchall, get_trainers_group
from api.crud.crud_semester import get_ongoing_semester
from sport.models import Sport, Student, Trainer, Group, Enroll


def get_sports(all=False, student: Optional[Student] = None):
    """
    Retrieves existing sport types
    @param all - If true, returns also special sport types
    @param student - if student passed, get sports applicable for student
    @return list of all sport types
    """
    groups = Group.objects.filter(semester__pk=api.crud.get_ongoing_semester().pk)
    if student:
        groups = groups.filter(allowed_medical_groups=student.medical_group_id)
        # groups = groups.filter(allowed_qr__in=[-1, int(student.has_QR)])

    # w/o distinct returns a lot of duplicated
    sports = Sport.objects.filter(id__in=groups.values_list('sport')).distinct()
    if not all:
        sports = sports.filter(special=False, visible=True)

    sports_list = []
    for sport in sports.all().values():
        sport_groups = groups.filter(sport=sport['id'])

        trainers = set()
        for group_trainers in sport_groups.values_list('trainers'):
            trainers |= set(group_trainers)

        try:
            trainers = list(map(lambda t: Trainer.objects.get(user_id=t), trainers))
        except Trainer.DoesNotExist:
            trainers = []

        sport['trainers'] = trainers
        sport['num_of_groups'] = sport_groups.count()
        sport['free_places'] = get_free_places_for_sport(sport['id'])

        sports_list.append(sport)

    return sports_list


def get_student_groups(student: Student):
    """
    Retrieves groups, where student is enrolled
    @return list of group dicts
    """
    with connection.cursor() as cursor:
        cursor.execute('SELECT '
                       'g.id AS id, '
                       'g.name AS name, '
                       's.name AS sport_name '
                       'FROM enroll e, "group" g, sport s '
                       'WHERE g.semester_id = current_semester() '
                       'AND e.group_id = g.id '
                       'AND e.student_id = %s '
                       'AND s.id = g.sport_id ', (student.pk,))
        return dictfetchall(cursor)


def get_trainer_groups(trainer: Trainer):
    """
    For a given trainer return all groups he/she is training in current semester
    @return list of group trainer is trainings in current semester
    """
    groups = Group.objects.filter(
        semester__id=get_ongoing_semester().id,
        trainers__pk=trainer.pk,
    )
    return [{
        'id': group.pk,
        'name': group.to_frontend_name()
    } for group in groups]
    # Currently query is a list of one dictionary
    # Will it be converted to a dictionary?


def get_free_places_for_sport(sport_id):
    groups = Group.objects.filter(sport=sport_id, semester=get_ongoing_semester())
    res = 0
    # TODO: replace with aggregate
    for i in groups:
        res += i.capacity - Enroll.objects.filter(group=i.id).count()
    return res
