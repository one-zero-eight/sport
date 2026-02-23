from datetime import datetime, timedelta
from typing import Optional

from django.db import connection
from django.db.models import Q, Prefetch, Count
from django.utils import timezone

from api_v2.crud.crud_semester import get_current_semester_crud
from api_v2.crud.utils import dictfetchone, dictfetchall, get_trainers_group
from sport.models import Student, Trainer, Group, Training, TrainingCheckIn, Schedule
from accounts.models import User
from django.utils.html import strip_tags


def get_group_info(group_id: int):
    """
    Retrieves more detailed group info by its id
    """
    current_semester = get_current_semester_crud()
    
    try:
        group = Group.objects.select_related(
            'sport',
            'semester'
        ).prefetch_related(
            'trainers__user',
            'allowed_medical_groups'
        ).get(
            id=group_id,
            semester=current_semester
        )
    except Group.DoesNotExist:
        return None
    
    return {
        'id': group.id,
        'name': group.name,
        'capacity': group.capacity,
        'is_club': group.is_club,
        'accredited': group.accredited,
        'sport_id':  group.sport.id if group.sport else None,
        'sport_name': group.sport.name if group.sport else None,
        'semester': {
            'id': group.semester.id,
            'name': group.semester.name,
        },
        'schedule': Schedule.objects.filter(group_id=group_id).all(),
        'trainers': get_trainers_group(group_id),
        'description': strip_tags(group.sport.description) if group.sport and group.sport.description else '',
        'allowed_medical_groups': [mg.name for mg in group.allowed_medical_groups.all()],
        # 'allowed_education_level': group.allowed_education_level,
    }

# def get_group_info(group_id: int, student: Student):
#     """
#     Retrieves more detailed group info by its id
#     @param group_id - searched group id
#     @param student - request sender student
#     @return found group
#     """
#     with connection.cursor() as cursor:
#         cursor.execute(
#             'SELECT '
#             'g.id AS group_id, '
#             'g.name AS group_name, '
#             'g.capacity AS capacity, '
#             'g.is_club AS is_club, '
#             'count(e.id) AS current_load, '
#             'd.first_name AS trainer_first_name, '
#             'd.last_name AS trainer_last_name, '
#             'd.email AS trainer_email, '
#             'COALESCE(bool_or(e.student_id = %(student_id)s), false) AS is_enrolled '
#             'FROM "group" g '
#             'LEFT JOIN enroll e ON e.group_id = %(group_id)s '
#             'LEFT JOIN auth_user d ON g.trainer_id = d.id '
#             'WHERE g.id = %(group_id)s '
#             'GROUP BY g.id, d.id', {"group_id": group_id, "student_id": student.pk})

#         info = dictfetchone(cursor)
#         if info is None:
#             return None
            
#         info['trainers'] = get_trainers_group(group_id)

#         info['can_enroll'] = student.sport is not None and \
#             student.sport == Group.objects.get(id=info['group_id']).sport and \
#             not Group.objects.filter(enrolls__student=student,
#                                      semester=get_current_semester_crud()).exists()

#         return info


_week_delta = timedelta(days=7)


def can_check_in(
    student: Student, training: Training, student_checkins=None, time_now=None
):
    """Determines if a student can check into a training session based on several criteria."""
    time_now = time_now or timezone.now()
    t_date = training.start.date()

    # The training must not be finished yet, and you can check in only during 1 week before the training start
    if not (training.start < (time_now + _week_delta) and time_now < training.end):
        return False

    # The training must have free places left
    free_places = training.group.capacity - training.checkins.count()
    if free_places <= 0:
        return False

    student_checkins = student_checkins or (
        TrainingCheckIn.objects.filter(
            student=student, training__start__date=t_date
        ).select_related("training", "training__group__sport")
    )

    # The student can only get 4 hours at one day
    total_hours = sum(
        c.training.academic_duration
        for c in student_checkins
        if c.training.start.date() == t_date
    )
    if total_hours + training.academic_duration > 4:
        return False

    # The student can only get 2 hours at one day for the same sport type
    t_sport_id = training.group.sport.id if training.group.sport else None
    same_type_hours = sum(
        c.training.academic_duration
        for c in student_checkins
        if c.training.group.sport.id == t_sport_id and c.training.start.date() == t_date
    )
    if same_type_hours + training.academic_duration > 2:
        return False

    # Students in "Banned students" list are always prohibited
    banned_students = training.group.banned_students.all()
    if student in banned_students:
        return False

    # Students in "Allowed students" list can check in, no matter their medical group or gender
    allowed_students = training.group.allowed_students.all()
    if student in allowed_students:
        return True  # Allow

    # Other students must be of allowed medical groups and allowed gender
    allowed_medical_groups = training.group.allowed_medical_groups.all()
    return (
        student.medical_group in allowed_medical_groups and
        training.group.allowed_gender in (student.gender, -1)
    )



def get_trainings_for_student(student: Student, start, end, trainer: Optional[Trainer] = None):

    semester_id = get_current_semester_crud().id

    trainings = (
        Training.objects
        .select_related(
            "group",
            "group__sport",
            "training_class",
        )
        .prefetch_related(
            "group__allowed_medical_groups",
            "checkins",
        )
        .annotate(load=Count("checkins"))
        .filter(
            (
                Q(start__range=(start, end))
                | Q(end__range=(start, end))
                | (Q(start__lte=start) & Q(end__gte=end))
            ),
            ~Q(group__sport=None),
            (
                Q(group__allowed_medical_groups=student.medical_group)
                | Q(group__allowed_students=student.pk)
            ),
            group__semester=semester_id,
        )
        .exclude(group__banned_students=student.pk)
        .distinct()
    )

    student_checkins = TrainingCheckIn.objects.filter(
        student=student,
        training__start__range=(start, end)
    ).select_related("training", "training__group__sport")

    student_checkins_map = {c.training_id: c for c in student_checkins}

    trainings_data = []
    time_now = timezone.now()

    for t in trainings:

        trainings_data.append({
            "id": t.id,
            "start": t.start,
            "end": t.end,

            "group__id": t.group.id,
            "group_name": t.group.to_frontend_name(),

            "group__sport__id": t.group.sport.id if t.group.sport else None,
            "sport_name": t.group.sport.name if t.group.sport else None,

            "training_class__id": t.training_class.id if t.training_class else None,
            "training_class": t.training_class.name if t.training_class else None,

            "capacity": t.group.capacity,
            "is_club": t.group.is_club,
            "custom_name": t.group.name,
            "load": t.load,

            "group_accredited": t.group.accredited,
            "can_grade": False,
            "can_check_in": can_check_in(student, t, student_checkins, time_now),
            "checked_in": t.id in student_checkins_map,
        })

    return trainings_data


def get_trainings_for_trainer(trainer: Trainer, start, end):

    trainings = (
        Training.objects
        .select_related(
            "group",
            "group__sport",
            "training_class",
        )
        .annotate(load=Count("checkins"))
        .filter(
            group__semester__id=get_current_semester_crud().id,
            group__trainers=trainer,
        )
        .filter(
            Q(start__gt=start, start__lt=end)
            | Q(end__gt=start, end__lt=end)
            | Q(start__lt=start, end__gt=end)
        )
    )

    return [{
        "id": t.id,
        "start": t.start,
        "end": t.end,

        "group__id": t.group.id,
        "group_name": t.group.to_frontend_name(),

        "group__sport__id": t.group.sport.id if t.group.sport else None,
        "sport_name": t.group.sport.name if t.group.sport else None,

        "training_class__id": t.training_class.id if t.training_class else None,
        "training_class": t.training_class.name if t.training_class else None,

        "capacity": t.group.capacity,
        "is_club": t.group.is_club,
        "custom_name": t.group.name,
        "load": t.load,

        # personal-only
        "group_accredited": t.group.accredited,
        "can_grade": True,
        "can_check_in": True,
        "checked_in": False,
    } for t in trainings]


def get_students_grades(training_id: int):
    """
    Retrieves student grades for specific training
    @param training_id - searched training id
    @return list of student grades
    """
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT 
                u.id AS student_id,
                u.first_name,
                u.last_name,
                u.email,
                COALESCE(a.hours, 0) AS hours,
                m.id AS med_group_id,
                m.name AS med_group_name,
                m.description AS med_group_description
            FROM auth_user u
            JOIN student s ON s.user_id = u.id
            LEFT JOIN medical_group m ON m.id = s.medical_group_id
            LEFT JOIN attendance a 
                ON a.student_id = u.id AND a.training_id = %(training_id)s
            WHERE u.id IN (
                SELECT student_id FROM attendance WHERE training_id = %(training_id)s
                UNION
                SELECT student_id FROM sport_trainingcheckin WHERE training_id = %(training_id)s
            )
        """, {"training_id": training_id})

        rows = dictfetchall(cursor)

        for row in rows:
            row["id"] = row.pop("student_id")
            if row.get("med_group_id") is not None:
                row["medical_group"] = {
                    "id": row.pop("med_group_id"),
                    "name": row.pop("med_group_name"),
                    "description": row.pop("med_group_description"),
                }
            else:
                row["medical_group"] = None

        return rows



def get_student_last_attended_dates(group_id: int):
    """
    Retrieves last attended dates for students
    @param group_id - searched group id
    @return list of students and their last attended training timestamp
    """
    with connection.cursor() as cursor:
        cursor.execute('SELECT '
                       'd.id AS student_id, '
                       'd.first_name AS first_name, '
                       'd.last_name AS last_name, '
                       'd.email AS email, '
                       'max(t.start) AS last_attended, '
                       'concat(d.first_name, \' \', d.last_name) as full_name '
                       'FROM enroll e, auth_user d '
                       'LEFT JOIN attendance a ON a.student_id = d.id '
                       'LEFT JOIN training t ON a.training_id = t.id AND t.group_id = %(group_id)s '
                       'WHERE e.group_id = %(group_id)s '
                       'AND e.student_id = d.id '
                       'GROUP BY d.id', {"group_id": group_id})
        return dictfetchall(cursor)


def get_weekly_schedule_with_participants(user: User, student: Optional[Student] = None, trainer: Optional[Trainer] = None, start: Optional[datetime] = None, end: Optional[datetime] = None):
    """
    Retrieves weekly schedule with participants information for each training
    @param user - requesting user
    @param student - student object (if user is a student)
    @param trainer - trainer object (if user is a trainer)
    @param start - week start date
    @param end - week end date
    @return list of trainings with participants info
    """
    # Validate required parameters
    if start is None or end is None:
        return []
    
    # Get trainings for the week based on user type(s)
    student_trainings = []
    trainer_trainings = []
    
    if student:
        student_trainings = get_trainings_for_student(student, start, end, trainer)
    
    if trainer:
        trainer_trainings = get_trainings_for_trainer(trainer, start, end)
    
    # Combine trainings, giving priority to trainer role for can_grade
    combined_trainings = {}
    
    # Add student trainings first
    for training in student_trainings:
        combined_trainings[training['id']] = training
    
    # Add trainer trainings, overwriting can_grade if user is trainer for this group
    for training in trainer_trainings:
        if training['id'] in combined_trainings:
            # User is both student and trainer for this training
            # Keep trainer's can_grade=True
            combined_trainings[training['id']]['can_grade'] = True
        else:
            # User is only trainer for this training
            combined_trainings[training['id']] = training
    
    trainings = list(combined_trainings.values())
    
    # For each training, get participants info
    for training in trainings:
        training_id = training['id']
        
        # Get checked-in students and those who received grades
        participants = get_students_grades(training_id)
        
        # Add participants info to training
        training['participants'] = {
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
        
        # Add group capacity info
        try:
            group = Group.objects.get(id=training['group_id'])
            training['capacity'] = group.capacity
            training['available_spots'] = group.capacity - training['participants']['total_checked_in']
        except Group.DoesNotExist:
            training['capacity'] = 0
            training['available_spots'] = 0

    # Sort trainings by start time
    trainings.sort(key=lambda t: t['start'])
    return trainings
