from typing import Optional
from datetime import datetime

from django.db import connection
from django.db.models import F, IntegerField
from django.db.models import Q
from django.db.models import Count
from django.db.models import Prefetch

from api_v2.crud.utils import dictfetchall
from api_v2.crud import get_current_semester_crud
from sport.models import Student, Group, Schedule, Training


def get_sport_calendar(
        sport_id: int,
        student: Optional[Student] = None,
):
    """
    Retrieves existing schedules for the given sport type
    @param sport_id - searched sport id
    @param student - student, acquiring groups. Groups will be based on medical group
    @return list of trainings info
    """

    medical_group_condition = Q(allowed_medical_groups__id=1) | Q(allowed_medical_groups__id=2)
    qr_condition = Q(allowed_qr=-1)
    if student is not None:
        medical_group_condition = Q(allowed_medical_groups__id=student.medical_group.id)
        qr_condition = Q(allowed_qr__in=[-1, int(student.has_QR)])

    prefetch_query = Schedule.objects.select_related('training_class')
   
    query = Group.objects.prefetch_related(
        'sport',
        'enrolls',
        Prefetch('schedule', queryset=prefetch_query),
    ).filter(
        (Q(sport__id=sport_id) if sport_id != -1 else Q(sport=None)) &
        medical_group_condition &
        # qr_condition &
        Q(schedule__isnull=False) &
        Q(semester__id=get_current_semester_crud().id)
    ).values(
        'id',
        'name',
        'capacity',
        'schedule__weekday',
        'schedule__start',
        'schedule__end',
        'schedule__training_class__name',
    ).annotate(
        current_load=Count('enrolls__id'),
        group_id=F('id'),
        group_name=F('name'),
        weekday=F('schedule__weekday'),
        start=F('schedule__start'),
        end=F('schedule__end'),
        training_class=F('schedule__training_class__name'),
    ).order_by(
        'id',
        'schedule__id',
        'schedule__training_class__id',
    ).values(
        'capacity',
        'current_load',
        'group_id',
        'group_name',
        'weekday',
        'start',
        'end',
        'training_class',
    )

    return list(query)

def get_sport_schedule(
        sport_id: Optional[int] = None,
        student: Optional[Student] = None,
        start_time: datetime = datetime.now(), 
        end_time: datetime = datetime.now()
    ): 

    if not isinstance(start_time, datetime):
        print("start_time is not datetime")
    if not isinstance(end_time, datetime):
        print("end time is not datetime")
    query = Training.objects.select_related(
        'group',
        'group__sport',
        'training_class'
    ).filter(
        start__gte=start_time,
        end__lte=end_time
    )

    if sport_id is not None and sport_id != 0:
        query = query.filter(group__sport__id=sport_id)
    
    if student is not None and hasattr(student, 'medical_group'):
        student_medical_group_id = student.medical_group.id
        query = query.filter(
            Q(group__allowed_medical_groups__id=student_medical_group_id) |
            Q(group__allowed_medical_groups__isnull=True)
        ).distinct()

    query = query.annotate(
        sport_name=F('group__sport__name'),
        group_name=F('group__name'),
        capacity=F('group__capacity'),
        is_club=F('group__is_club'),
        load=Count('checkins', distinct=True),
    ).values(
        'id',
        'start',
        'end',
        'group__id',
        'group_name',
        'capacity',
        'custom_name',
        'load',
        'is_club',
        'sport_name',
        'group__sport__id',
        'training_class__name',
        'training_class__id',
    ).order_by('start')

    return list(query)

