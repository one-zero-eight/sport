from django.db.models import F
from django.db.models.expressions import Subquery
from django.db.models.fields import IntegerField
from sport.models import Training, Group


class SumSubquery(Subquery):
    output_field = None

    def __init__(self, queryset, sum_by, output_field=IntegerField(), **extra):
        super().__init__(queryset, output_field, **extra)
        self.output_field = output_field
        self.template = "(SELECT sum({}) FROM (%(subquery)s) _sum)".format(sum_by)


def dictfetchall(cursor):
    """Return all rows from a cursor as a dict"""
    columns = [col[0] for col in cursor.description]
    return [
        dict(zip(columns, row))
        for row in cursor.fetchall()
    ]


def dictfetchone(cursor):
    """Return one rows from a cursor as a dict"""
    columns = [col[0] for col in cursor.description]
    row = cursor.fetchone()
    return dict(zip(columns, row)) if row is not None else None

def get_trainers(training_id: int):
    """
    Return the list of dictionaries containing trainers' information
    """
    query = Training.objects.get(
        id=training_id,
    ).group.trainers.annotate(
        trainer_first_name=F('user__first_name'),
        trainer_last_name=F('user__last_name'),
        trainer_email=F('user__email'),
    ).values('trainer_first_name', 'trainer_last_name', 'trainer_email')

    return list(query)


def get_trainers_group(group_id: int):
    """
    Return the list of dictionaries containing trainers' information
    """
    query = Group.objects.get(
        id=group_id,
    ).trainers.annotate(
        trainer_first_name=F('user__first_name'),
        trainer_last_name=F('user__last_name'),
        trainer_email=F('user__email'),
    ).values(
        'trainer_first_name',
        'trainer_last_name',
        'trainer_email',
    )

    return list(query)
