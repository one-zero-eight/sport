from typing import Optional

from django.conf import settings
from django.db import connection
from django.db.models import F
from django.db.models import Q
from django.db.models import Count, Sum, IntegerField

import api.crud
from api.crud.utils import dictfetchall, get_trainers_group
from api.crud.crud_semester import get_ongoing_semester
from sport.models import Sport, Student, Trainer, Group, Enroll, Training


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


def get_sports_with_groups(student: Optional[Student] = None):
    """
    Retrieves all sports with their groups and detailed information
    @param student - if student passed, get sports applicable for student
    @return list of sports with groups, schedules, trainers, etc.
    """
    from sport.models import Schedule, TrainingClass
    
    # Get groups for current semester
    groups = Group.objects.filter(semester__pk=api.crud.get_ongoing_semester().pk)
    if student:
        groups = groups.filter(allowed_medical_groups=student.medical_group_id)
    
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
            # Get schedule for this group
            schedule_data = []
            for schedule in group.schedule.all():
                # Get training IDs for this schedule
                training_ids = list(Training.objects.filter(
                    schedule=schedule,
                    group=group
                ).values_list('id', flat=True))
                
                schedule_info = {
                    'weekday': schedule.weekday,
                    'weekday_name': schedule.get_weekday_display(),
                    'start_time': schedule.start.strftime('%H:%M'),
                    'end_time': schedule.end.strftime('%H:%M'),
                    'training_class': schedule.training_class.name if schedule.training_class else None,
                    'training_ids': training_ids,
                    #'location': schedule.training_class.name if schedule.training_class else None,  # Location is same as training_class
                }
                schedule_data.append(schedule_info)
            
            # Get trainers for this group
            trainers_data = []
            for trainer in group.trainers.all():
                trainer_info = {
                    'id': trainer.user.id,
                    'name': f"{trainer.user.first_name} {trainer.user.last_name}",
                    'email': trainer.user.email,
                }
                trainers_data.append(trainer_info)
            
            # Add main trainer if exists
            if group.trainer and group.trainer not in group.trainers.all():
                main_trainer = {
                    'id': group.trainer.user.id,
                    'name': f"{group.trainer.user.first_name} {group.trainer.user.last_name}",
                    'email': group.trainer.user.email,
                }
                trainers_data.insert(0, main_trainer)  # Main trainer first
            
            # Calculate enrollment info
            current_enrollment = Enroll.objects.filter(group=group).count()
            free_places = group.capacity - current_enrollment
            
            # Check if student is enrolled
            is_enrolled = False
            if student:
                is_enrolled = Enroll.objects.filter(group=group, student=student).exists()
            
            group_info = {
                'id': group.id,
                'name': group.name or '',
                'description': group.sport.description if group.sport else '',
                'capacity': group.capacity,
                'current_enrollment': current_enrollment,
                'free_places': free_places,
                'is_club': group.is_club,
                'accredited': group.accredited,
                'is_enrolled': is_enrolled,
                'schedule': schedule_data,
                'trainers': trainers_data,
                'allowed_medical_groups': [mg.name for mg in group.allowed_medical_groups.all()],
            }
            groups_data.append(group_info)
        
        sport_info = {
            'id': sport.id,
            'name': sport.name,
            'description': sport.description,
            'groups': groups_data,
            'total_groups': len(groups_data),
            'total_free_places': sum(group['free_places'] for group in groups_data),
        }
        sports_list.append(sport_info)
    
    return sports_list
