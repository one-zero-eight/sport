from datetime import datetime, timedelta

from django.db import connection
from django.db.models import Q, Prefetch
from django.utils import timezone

from api.crud.crud_semester import get_ongoing_semester
from api.crud.utils import dictfetchone, dictfetchall, get_trainers_group
from sport.models import Student, Trainer, Group, Training, TrainingCheckIn


def get_group_info(group_id: int, student: Student):
    """
    Retrieves more detailed group info by its id
    @param group_id - searched group id
    @param student - request sender student
    @return found group
    """
    with connection.cursor() as cursor:
        cursor.execute(
            'SELECT '
            'g.id AS group_id, '
            'g.name AS group_name, '
            'g.capacity AS capacity, '
            'g.is_club AS is_club, '
            'count(e.id) AS current_load, '
            'd.first_name AS trainer_first_name, '
            'd.last_name AS trainer_last_name, '
            'd.email AS trainer_email, '
            'COALESCE(bool_or(e.student_id = %(student_id)s), false) AS is_enrolled '
            'FROM "group" g '
            'LEFT JOIN enroll e ON e.group_id = %(group_id)s '
            'LEFT JOIN auth_user d ON g.trainer_id = d.id '
            'WHERE g.id = %(group_id)s '
            'GROUP BY g.id, d.id', {"group_id": group_id, "student_id": student.pk})

        info = dictfetchone(cursor)
        info['trainers'] = get_trainers_group(group_id)

        info['can_enroll'] = student.sport is not None and \
            student.sport == Group.objects.get(id=info['group_id']).sport and \
            not Group.objects.filter(enrolls__student=student,
                                     semester=get_ongoing_semester()).exists()

        return info


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


def get_trainings_for_student(student: Student, start: datetime, end: datetime):
    # Assume current_semester() is a function that retrieves the current semester object.
    # Prefetch groups and allowed medical groups.
    group_prefetch = Prefetch("group", queryset=Group.objects.select_related("sport").prefetch_related(
        "allowed_medical_groups"))

    # Assuming TrainingCheckIn model has a 'student' and 'training' foreign key.
    # And Training has a 'group' foreign key with an 'allowed_medical_groups' many-to-many field.
    semester_id = get_ongoing_semester().id
    trainings = (
        Training.objects.filter(
            # Filter by requested time range
            Q(start__range=(start, end))
            | Q(end__range=(start, end))
            | (Q(start__lte=start) & Q(end__gte=end)),
            # Do not show 'Self training', 'Extra sport events', 'Medical leave', etc. trainings
            ~Q(group__sport=None),
            # The student must either have acceptable medical group
            Q(group__allowed_medical_groups=student.medical_group)
            # ... or be in 'Allowed students' list
            | Q(group__allowed_students=student.pk),
            # Show only for current semester
            group__semester=semester_id,
        )
        # Do not show the training if a student is in 'Banned students' list
        .exclude(group__banned_students=student.pk)
        .prefetch_related(
            group_prefetch,
            "training_class",
            "checkins",
        )
    )

    # get all student check-ins for the given time range
    student_checkins = (
        TrainingCheckIn.objects.filter(student=student, training__start__range=(start, end))
        .select_related("training", "training__group__sport")
    )
    student_checkins_map = {checkin.training_id: checkin for checkin in student_checkins}

    trainings_data = []
    time_now = timezone.now()

    for t in trainings:
        # Example of calculating can_check_in data. You need to adapt this to your actual model structure and data.
        # This is a placeholder for the logic to calculate the necessary data for can_check_in.
        can_check_in_result = can_check_in(student, t, student_checkins, time_now)
        group_frontend_name = t.group.to_frontend_name()

        training_dict = {
            "id": t.id,
            "start": t.start,
            "end": t.end,
            "group_id": t.group.id,
            "group_name": group_frontend_name,
            "training_class": t.training_class.name if t.training_class else None,
            "group_accredited": t.group.accredited,
            "can_grade": False,
            "can_check_in": can_check_in_result,
            "checked_in": student_checkins_map.get(t.id) is not None,
        }
        trainings_data.append(training_dict)
    return trainings_data


def get_trainings_for_trainer(trainer: Trainer, start: datetime, end: datetime):
    """
    Retrieves existing trainings in the given range for given student
    @param trainer - searched trainer
    @param start - range start date
    @param end - range end date
    @return list of trainings for trainer
    """
    trainings = Training.objects.select_related(
        'group',
        'training_class',
    ).filter(
        Q(group__semester__id=get_ongoing_semester().id) &
        Q(group__trainers=trainer) & (
            Q(start__gt=start) & Q(start__lt=end) |
            Q(end__gt=start) & Q(end__lt=end) |
            Q(start__lt=start) & Q(end__gt=end)
        )
    )
    return [{
        'id': e.id,
        'start': e.start,
        'end': e.end,
        'group_id': e.group_id,
        'group_name': e.group.to_frontend_name(),
        'training_class': e.training_class.name if e.training_class else None,
        'group_accredited': e.group.accredited,
        'can_grade': True,
    } for e in trainings]


def get_students_grades(training_id: int):
    """
    Retrieves student grades for specific training
    @param training_id - searched training id
    @return list of student grades
    """
    with connection.cursor() as cursor:
        cursor.execute('SELECT '
                       'd.id AS student_id, '
                       'd.first_name AS first_name, '
                       'd.last_name AS last_name, '
                       'd.email AS email, '
                       'a.hours AS hours, '
                       'm.name AS med_group, '
                       'concat(d.first_name, \' \', d.last_name) as full_name '
                       'FROM training t, attendance a, auth_user d, student s '
                       'LEFT JOIN medical_group m ON m.id = s.medical_group_id '
                       'WHERE s.user_id = a.student_id '
                       'AND d.id = a.student_id '
                       'AND a.training_id = %(training_id)s '
                       'AND t.id = %(training_id)s '
                       'UNION DISTINCT '
                       'SELECT '
                       'd.id AS student_id, '
                       'd.first_name AS first_name, '
                       'd.last_name AS last_name, '
                       'd.email AS email, '
                       'COALESCE(a.hours, 0) AS hours, '
                       'm.name AS med_group, '
                       'concat(d.first_name, \' \', d.last_name) as full_name '
                       'FROM training t, sport_trainingcheckin e, auth_user d, student s '
                       'LEFT JOIN attendance a ON a.student_id = s.user_id AND a.training_id = %(training_id)s '
                       'LEFT JOIN medical_group m ON m.id = s.medical_group_id '
                       'WHERE s.user_id = e.student_id '
                       'AND d.id = e.student_id '
                       'AND t.id = %(training_id)s '
                       'AND t.id = e.training_id ', {"training_id": training_id})
        return dictfetchall(cursor)


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
