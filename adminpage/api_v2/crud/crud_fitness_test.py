import datetime
import logging

from django.db.models import Q

from api_v2.crud import get_current_semester_crud
from sport.models import FitnessTestResult, FitnessTestExercise, FitnessTestGrading, Student, FitnessTestSession, \
    Semester

logger = logging.getLogger(__name__)


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

    errors = []
    for res in results:
        logger.info(f"Processing result: student_id={res['student_id']}, exercise_id={res['exercise_id']}, value={res['value']}")
        
        try:
            student = Student.objects.get(user__id=res['student_id'])
            logger.info(f"Found student: {student}")
        except Student.DoesNotExist:
            error_msg = f"Student with user_id={res['student_id']} does not exist"
            logger.error(error_msg)
            errors.append(error_msg)
            continue
            
        try:
            exercise = FitnessTestExercise.objects.get(id=res['exercise_id'])
            logger.info(f"Found exercise: {exercise}")
        except FitnessTestExercise.DoesNotExist:
            error_msg = f"Exercise with id={res['exercise_id']} does not exist"
            logger.error(error_msg)
            errors.append(error_msg)
            continue

        FitnessTestResult.objects.update_or_create(
            exercise=exercise,
            student=student,
            defaults={'value': res['value']},
            session=session
        )

    if errors:
        raise ValueError("; ".join(errors))

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
