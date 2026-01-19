import datetime
import logging
from collections import defaultdict
from typing import Any, Dict, List, Optional

from django.db.models import Q
from django.utils import timezone

from sport.models import (
    FitnessTestResult,
    FitnessTestExercise,
    FitnessTestGrading,
    Student,
    FitnessTestSession,
    Semester,
)

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
        logger.info(
            f"Processing result: student_id={res['student_id']}, "
            f"exercise_id={res['exercise_id']}, value={res['value']}"
        )

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
    return FitnessTestGrading.objects.filter(
        Q(gender__exact=-1) | Q(gender__exact=student.gender),
        exercise=result.exercise
    )


def get_score(student: Student, result: FitnessTestResult):
    try:
        return get_grading_scheme(student, result).get(
            start_range__lte=result.value,
            end_range__gt=result.value
        ).score
    except FitnessTestGrading.DoesNotExist:
        return 0  # Default score when grading scheme is not found


def get_max_score(student: Student, result: FitnessTestResult):
    scores = get_grading_scheme(student, result).values_list('score', flat=True)
    return max(scores) if scores else 0  # Default max score when grading scheme is not found


def _fitness_result_to_student_exercise_dict(result: FitnessTestResult) -> Dict[str, Any]:
    """
    Под сериализатор FitnessTestStudentExerciseResult:
    exercise_id, exercise_name, unit, value
    """
    ex: FitnessTestExercise = result.exercise
    return {
        "exercise_id": ex.id,
        "exercise_name": ex.exercise_name,
        "unit": ex.value_unit,
        "value": result.value,
    }


def get_current_semester_crud(*, now=None) -> Optional[Semester]:
    if now is None:
        now = timezone.localdate()

    qs = Semester.objects.all()

    current = qs.filter(start__lte=now, end__gte=now).order_by("-start")
    if current.exists():
        return current.first()

    latest = qs.order_by("-start")
    return latest.first() if latest.exists() else None


def get_student_fitness_results_for_semester_crud(
    *,
    student: Student,
    semester: Semester,
    latest_only: bool = False,
) -> List[Dict[str, Any]]:
    sessions_qs = (
        FitnessTestSession.objects
        .filter(semester=semester)
        .select_related("semester")
        .order_by("-date", "-id")
    )

    sessions = list(sessions_qs[:1] if latest_only else sessions_qs)
    if not sessions:
        return []

    results_qs = (
        FitnessTestResult.objects
        .filter(student=student, session__in=sessions)
        .select_related("exercise", "session", "session__semester")
        .order_by("-session__date", "exercise__id")
    )

    by_session_id: Dict[int, List[Dict[str, Any]]] = defaultdict(list)
    for r in results_qs:
        by_session_id[r.session_id].append(_fitness_result_to_student_exercise_dict(r))

    return [
        {
            "session": s,
            "exercise_results": by_session_id.get(s.id, []),
        }
        for s in sessions
    ]


def get_student_fitness_results_for_current_semester_crud(
    *,
    student: Student,
    latest_only: bool = False,
) -> List[Dict[str, Any]]:
    semester = get_current_semester_crud()
    if not semester:
        return []
    return get_student_fitness_results_for_semester_crud(
        student=student,
        semester=semester,
        latest_only=latest_only,
    )


def get_student_fitness_results_for_all_semesters_crud(
    *,
    student: Student,
    semester_ids: Optional[List[int]] = None,
    latest_only: bool = False,
) -> Dict[int, List[Dict[str, Any]]]:
    sessions_qs = FitnessTestSession.objects.all().select_related("semester")
    if semester_ids is not None:
        sessions_qs = sessions_qs.filter(semester_id__in=semester_ids)

    sessions_qs = sessions_qs.order_by("semester_id", "-date", "-id")
    sessions = list(sessions_qs)
    if not sessions:
        return {}

    if latest_only:
        seen = set()
        filtered = []
        for s in sessions:
            if s.semester_id in seen:
                continue
            seen.add(s.semester_id)
            filtered.append(s)
        sessions = filtered

    results_qs = (
        FitnessTestResult.objects
        .filter(student=student, session__in=sessions)
        .select_related("exercise", "session", "session__semester")
        .order_by("session__semester_id", "-session__date", "exercise__id")
    )

    by_session_id: Dict[int, List[Dict[str, Any]]] = defaultdict(list)
    for r in results_qs:
        by_session_id[r.session_id].append(_fitness_result_to_student_exercise_dict(r))

    by_semester: Dict[int, List[Dict[str, Any]]] = defaultdict(list)
    for s in sessions:
        by_semester[s.semester_id].append(
            {
                "session": s,
                "exercise_results": by_session_id.get(s.id, []),
            }
        )

    return dict(by_semester)
