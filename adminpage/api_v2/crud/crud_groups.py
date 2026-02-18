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


def get_clubs_as_trainings(student: Optional[Student] = None):
    """
    Retrieve all upcoming club trainings in the same format as weekly schedule
    @param student - if student passed, filter applicable trainings
    @return list of training objects with participants info
    """
    from sport.models import TrainingCheckIn
    from django.db.models import Prefetch
    
    # Get current time to filter out past trainings
    current_time = timezone.now()
    
    # Get groups for current semester that are clubs
    groups_query = Group.objects.filter(
        semester__pk=get_current_semester_crud().pk,
        is_club=True  # Only clubs
    )
    
    if student:
        groups_query = groups_query.filter(
            Q(allowed_medical_groups=student.medical_group)
            | Q(allowed_students=student.pk)
        ).exclude(banned_students=student.pk)
    
    # Get upcoming trainings for these club groups
    group_prefetch = Prefetch("group", queryset=Group.objects.select_related("sport").prefetch_related(
        "allowed_medical_groups"))
    
    trainings = Training.objects.filter(
        group__in=groups_query,
        start__gt=current_time,  # Only future trainings
        group__sport__isnull=False  # Exclude special groups
    ).select_related(
        'group', 'group__sport', 'training_class'
    ).prefetch_related(
        group_prefetch, "checkins"
    ).order_by('start')
    
    # Get student check-ins if student provided
    student_checkins_map = {}
    if student:
        student_checkins = TrainingCheckIn.objects.filter(
            student=student, 
            training__in=trainings
        ).select_related("training")
        student_checkins_map = {checkin.training_id: checkin for checkin in student_checkins}
    
    trainings_data = []
    
    for training in trainings:
        # Calculate can_check_in
        can_check_in_result = False
        checked_in = False
        
        if student:
            can_check_in_result = can_check_in(student, training)
            checked_in = training.id in student_checkins_map
        
        # Get current enrollment for this group
        # current_enrollment = Enroll.objects.filter(group=training.group).count()
        
        # Calculate participants info (similar to weekly schedule)
        from api_v2.crud.crud_training import get_students_grades
        participants = get_students_grades(training.id)
        
        participants_info = {
            'total_checked_in': len([p for p in participants if p.get('hours', 0) >= 0]),
            'students': [
                {
                    'id': p['student_id'],
                    'name': p['full_name'],
                    'email': p['email'],
                    'medical_group': p['med_group'],
                    'hours': p.get('hours', 0),
                    'attended': p.get('hours', 0) > 0
                }
                for p in participants
            ]
        }
        
        training_dict = {
            "id": training.id,
            "start": training.start,
            "end": training.end,
            "group_id": training.group.id,
            "group_name": training.group.to_frontend_name(),
            "training_class": training.training_class.name if training.training_class else None,
            "group_accredited": training.group.accredited,
            "can_grade": False,  # Students can't grade
            "can_check_in": can_check_in_result,
            "checked_in": checked_in,
            "capacity": training.group.capacity,
            "available_spots": training.group.capacity - participants_info['total_checked_in'],
            "participants": participants_info
        }
        trainings_data.append(training_dict)
    
    return trainings_data


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
    current_time = timezone.now()
    
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
            group_trainings = []
            trainings = Training.objects.filter(
                group=group,
                start__gt=current_time  # Only future trainings
            ).select_related('training_class').order_by('start')
            
            for training in trainings:
                # Get participants info for this training
                from api_v2.crud.crud_training import get_students_grades
                participants = get_students_grades(training.id)
                
                participants_info = {
                    'total_checked_in': len([p for p in participants if p.get('hours', 0) >= 0]),
                    'students': [
                        {
                            'id': p['student_id'],
                            'name': p['full_name'],
                            'email': p['email'],
                            'medical_group': p['med_group'],
                            'hours': p.get('hours', 0),
                            'attended': p.get('hours', 0) > 0
                        }
                        for p in participants
                    ]
                }
                
                # Calculate can_check_in and checked_in for student
                can_check_in_result = False
                checked_in = False
                if student:
                    can_check_in_result = can_check_in(student, training)
                    from sport.models import TrainingCheckIn
                    checked_in = TrainingCheckIn.objects.filter(
                        student=student, training=training
                    ).exists()
                
                training_info = {
                    'id': training.id,
                    'start': training.start,
                    'end': training.end,
                    'training_class': training.training_class.name if training.training_class else None,
                    'group_accredited': group.accredited,
                    'can_grade': False,
                    'can_check_in': can_check_in_result,
                    'checked_in': checked_in,
                    'participants': participants_info,
                    'capacity': group.capacity,
                    'available_spots': group.capacity - participants_info['total_checked_in'],
                }
                group_trainings.append(training_info)
            
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
            # current_enrollment = Enroll.objects.filter(group=group).count()
            
            # Clean HTML tags from group name and description
            group_name = strip_tags(group.name) if group.name else ''
            group_description = strip_tags(group.sport.description) if group.sport and group.sport.description else ''
            
            group_info = {
                'id': group.id,
                'name': group_name,
                'description': group_description,
                'capacity': group.capacity,
                # 'current_enrollment': current_enrollment,s
                'is_club': group.is_club,
                'accredited': group.accredited,
                'trainings': group_trainings,
                'trainers': trainers_data,
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
