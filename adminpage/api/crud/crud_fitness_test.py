import datetime

from django.db.models import Q

from api.crud import get_ongoing_semester
from sport.models import FitnessTestResult, FitnessTestExercise, FitnessTestGrading, Student, FitnessTestSession, \
    Semester


def get_exercises_crud(semester_id):
    if semester_id is not None:
        return list(FitnessTestExercise.objects.filter(semester=semester_id))
    else:
        return list(FitnessTestExercise.objects.all())


def post_student_exercises_result_crud(semester, retake, results, session_id, teacher):
    session, created = FitnessTestSession.objects.get_or_create(
        id=session_id,
        defaults={
            'semester': semester,
            'teacher_id': teacher.id,
            'retake': retake,
            'date': datetime.datetime.now(),
        }
    )

    for res in results:
        student = Student.objects.get(user__id=res['student_id'])
        exercise = FitnessTestExercise.objects.get(id=res['exercise_id'])

        FitnessTestResult.objects.update_or_create(
            exercise=exercise,
            student=student,
            defaults={'value': res['value']},
            session=session
        )

    return session.id


def get_grading_scheme(student: Student, result: FitnessTestResult):
    return FitnessTestGrading.objects.filter(Q(gender__exact=-1) | Q(gender__exact=student.gender),
                                             exercise=result.exercise)


def get_score(student: Student, result: FitnessTestResult):
    try:
        return get_grading_scheme(student, result).get(start_range__lte=result.value, end_range__gt=result.value).score
    except FitnessTestGrading.DoesNotExist:
        return 0  # Default score when grading scheme is not found


def get_max_score(student: Student, result: FitnessTestResult):
    scores = get_grading_scheme(student, result).values_list('score', flat=True)
    return max(scores) if scores else 0  # Default max score when grading scheme is not found
