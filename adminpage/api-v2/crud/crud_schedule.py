from typing import Optional

from django.db import connection
from django.db.models import F, IntegerField
from django.db.models import Q
from django.db.models import Count
from django.db.models import Prefetch

from api.crud.utils import dictfetchall
from api.crud import get_ongoing_semester
from sport.models import Student, Group, Schedule


def get_sport_schedule(
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
        Q(semester__id=get_ongoing_semester().id)
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
