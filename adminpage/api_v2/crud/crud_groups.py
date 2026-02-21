from typing import Optional

from django.conf import settings
from django.db import connection
from django.db.models import F
from django.db.models import Q
from django.db.models import Count, Sum, IntegerField
from django.utils import timezone
from django.utils.html import strip_tags

import api_v2.crud
from api_v2.crud.utils import dictfetchall, get_trainers_group
from api_v2.crud.crud_semester import get_current_semester_crud
from sport.models import Sport, Student, Trainer, Group, Enroll, Training
from api_v2.crud.crud_training import can_check_in


def get_sports(all=False, student: Optional[Student] = None):
    """
    Retrieves existing sport types
    @param all - If true, returns also special sport types
    @param student - if student passed, get sports applicable for student
    @return list of all sport types
    """
    groups = Group.objects.filter(semester__pk=get_current_semester_crud().pk)
    if student:
        groups = groups.filter(allowed_medical_groups=student.medical_group)
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
        semester__id=get_current_semester_crud().id,
        trainers__pk=trainer.pk,
    )
    return [{
        'id': group.pk,
        'name': group.to_frontend_name()
    } for group in groups]
    # Currently query is a list of one dictionary
    # Will it be converted to a dictionary?


def get_free_places_for_sport(sport_id: int) -> int:
    """
    Calculate the total number of free places for all groups in a sport
    """
    groups = Group.objects.filter(
        sport=sport_id,
        semester=get_current_semester_crud()
    )
    
    total_free = 0
    for group in groups:
        current_enrollment = Enroll.objects.filter(group=group).count()
        free_places = max(0, group.capacity - current_enrollment)
        total_free += free_places
    
    return total_free


def get_sports_with_groups(student: Optional[Student] = None):
    """
    Retrieves all sports with their groups and detailed information
    @param student - if student passed, get sports applicable for student
    @return list of sports with groups, schedules, trainers, etc.
    """
    from sport.models import Schedule, TrainingClass
    
    # Get groups for current semester
    groups = Group.objects.filter(semester__pk=get_current_semester_crud().pk)
    if student:
        groups = groups.filter(allowed_medical_groups=student.medical_group)
    
    # Get sports that have groups
    sports = Sport.objects.filter(
        id__in=groups.values_list('sport', flat=True)
    ).filter(special=False, visible=True).distinct()
    
    sports_list = []
    
    for sport in sports:
        sport_groups = groups.filter(sport=sport).select_related(
            'trainer__user', 'sport'
        ).prefetch_related(
            'trainers__user', 'schedule', 'allowed_medical_groups'
        )
        
        # Prepare groups data
        groups_data = []
        for group in sport_groups:
            # Get trainings for this group - only upcoming trainings
            # Get trainers for this group
            
            # Clean HTML tags from group name and description
            group_name = strip_tags(group.name) if group.name else ''
            group_description = strip_tags(group.sport.description) if group.sport and group.sport.description else ''
            
            group_info = {
                'id': group.id,
                'name': group_name,
                'description': group_description,
                'capacity': group.capacity,
                'is_club': group.is_club,
                'accredited': group.accredited,
                'trainers': get_trainers_group(group.id),
                'allowed_medical_groups': [mg.name for mg in group.allowed_medical_groups.all()],
            }
            groups_data.append(group_info)
        
        # Clean HTML tags from sport name and description
        sport_name = strip_tags(sport.name) if sport.name else ''
        sport_description = strip_tags(sport.description) if sport.description else ''
        
        sport_info = {
            'id': sport.id,
            'name': sport_name,
            'description': sport_description,
            'groups': groups_data,
            'total_groups': len(groups_data),
        }
        sports_list.append(sport_info)
    
    return sports_list
