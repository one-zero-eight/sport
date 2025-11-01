import logging
from collections import defaultdict

from django.db.models import Q
from drf_spectacular.utils import extend_schema
from rest_framework import status, serializers
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response

from api_v2.permissions import (
    IsTrainer, IsStudent, IsSuperUser,
)
from api_v2.serializers import (
    NotFoundSerializer,
    ErrorSerializer, SuggestionSerializer,
)

from api_v2.crud import get_exercises_crud, post_student_exercises_result_crud, \
    get_email_name_like_students, get_current_semester_crud, get_score, get_max_score
from api_v2.serializers.attendance import SuggestionQueryFTSerializer
from api_v2.serializers.fitness_test import FitnessTestExerciseSerializer, FitnessTestSessionSerializer, \
    FitnessTestSessionWithResult, FitnessTestStudentResult, FitnessTestUpload, FitnessTestSessionWithGroupedResults
from api_v2.serializers.semester import SemesterInSerializer
from sport.models import FitnessTestSession, FitnessTestResult, FitnessTestExercise, Semester, Student

logger = logging.getLogger(__name__)


@extend_schema(
    methods=["GET"],
    tags=["Fitness Test"],
    summary="Get fitness test exercises",
    description="Get all fitness test exercises for a specific semester. If semester_id is not provided, returns exercises for the current semester.",
    parameters=[SemesterInSerializer],
    responses={
        status.HTTP_200_OK: FitnessTestExerciseSerializer(many=True),
    }
)
@api_view(["GET"])
def get_exercises(request, **kwargs):
    serializer = SemesterInSerializer(data=request.GET)
    serializer.is_valid(raise_exception=True)
    semester_id = serializer.validated_data.get('semester_id')

    if semester_id is None:
        semester_id = get_current_semester_crud()
    exercises = get_exercises_crud(semester_id)

    return Response(FitnessTestExerciseSerializer(exercises, many=True).data)


@extend_schema(
    methods=["GET"],
    tags=["Fitness Test"],
    summary="Get fitness test sessions",
    description="Get all fitness test sessions for a specific semester. If semester_id is not provided, returns all sessions. Only accessible by trainers.",
    parameters=[SemesterInSerializer],
    responses={
        status.HTTP_200_OK: FitnessTestSessionSerializer(many=True)
    }
)
@api_view(["GET"])
@permission_classes([IsTrainer | IsSuperUser])
def get_sessions(request, **kwargs):
    serializer = SemesterInSerializer(data=request.GET)
    serializer.is_valid(raise_exception=True)
    semester_id = serializer.validated_data.get('semester_id')

    if semester_id is None:
        sessions = FitnessTestSession.objects.all()
    else:
        sessions = FitnessTestSession.objects.filter(semester_id=semester_id)

    return Response(FitnessTestSessionSerializer(sessions, many=True).data)


@extend_schema(
    methods=["GET"],
    tags=["Fitness Test"],
    summary="Get student fitness test results",
    description="Get all fitness test results for the current student, grouped by semester and retake status, with detailed scores and grades.",
    responses={
        status.HTTP_200_OK: FitnessTestStudentResult(many=True),
        status.HTTP_404_NOT_FOUND: NotFoundSerializer(),
    }
)
@api_view(["GET"])
@permission_classes([IsStudent])
def get_result(request, **kwargs):
    results = FitnessTestResult.objects.filter(student_id=request.user.student.user_id)
    student = Student.objects.get(user__id=request.user.student.user_id)
    if not len(results):
        return Response(status=status.HTTP_404_NOT_FOUND)

    data = []
    for result_distinct_semester in results.values('exercise__semester_id', 'session__retake').distinct():
        semester_id = result_distinct_semester['exercise__semester_id']
        retake = result_distinct_semester['session__retake']

        semester = Semester.objects.get(id=semester_id)
        grade = True
        total_score = 0
        result_list = []
        for result in results.filter(exercise__semester_id=semester_id, session__retake=retake):
            # Safe handling of select values
            if result.exercise.select is None:
                display_value = result.value
            else:
                select_options = result.exercise.select.split(',')
                if 0 <= result.value < len(select_options):
                    display_value = select_options[result.value]
                else:
                    # Fallback to raw value if index is out of bounds
                    display_value = result.value
            
            result_list.append({
                'exercise': result.exercise.exercise_name,
                'unit': result.exercise.value_unit,
                'value': display_value,
                'score': get_score(request.user.student, result),
                'max_score': get_max_score(request.user.student, result),
            })
            grade = grade and result_list[-1]['score'] >= result.exercise.threshold
            total_score += result_list[-1]['score']

        if semester_id == get_current_semester_crud().id \
                and student.medical_group == 0 \
                and result_list:
            grade = True
        else:
            grade = grade and total_score >= semester.points_fitness_test

        data.append({
            'semester': semester.name,
            'retake': retake,
            'grade': grade,
            'total_score': total_score,
            'details': result_list,
        })

    return Response(data=data, status=status.HTTP_200_OK)


@extend_schema(
    methods=["GET"],
    tags=["Fitness Test"],
    summary="Get session details",
    description="Get detailed information about a specific fitness test session, including exercises and results.",
    responses={
        status.HTTP_200_OK: FitnessTestSessionWithGroupedResults()
    }
)
@api_view(["GET"])
@permission_classes([IsTrainer | IsSuperUser])
def get_session_info(request, session_id, **kwargs):
    # Get all results for this session
    results = FitnessTestResult.objects.filter(session_id=session_id).select_related('student__user', 'exercise')
    
    # Group results by student
    student_results = defaultdict(list)
    for result in results:
        student_id = result.student.user.id
        student_results[student_id].append({
            'exercise_id': result.exercise.id,
            'exercise_name': result.exercise.exercise_name,
            'unit': result.exercise.value_unit,
            'value': result.value
        })
    
    # Convert to the format expected by serializer
    results_dict = {}
    for student_id, exercise_results in student_results.items():
        # Get the student object (we can use any result from this student)
        student_result = next(r for r in results if r.student.user.id == student_id)
        results_dict[student_id] = {
            'student': student_result.student,
            'exercise_results': exercise_results
        }

    return Response(FitnessTestSessionWithGroupedResults({
        'session': FitnessTestSession.objects.get(id=session_id),
        'exercises': FitnessTestExercise.objects.filter(
            id__in=FitnessTestResult.objects.filter(session_id=session_id).values_list('exercise').distinct()
        ),
        'results': results_dict
    }).data)


# TODO: do same thing everywhere
class PostStudentExerciseResult(serializers.Serializer):
    result = serializers.CharField(default='ok')
    session_id = serializers.IntegerField()


@extend_schema(
    methods=["POST"],
    tags=["Fitness Test"],
    summary="Post student fitness test results",
    description="Post the results of a student's fitness test exercises for a specific session. Only accessible by trainers.",
    request=FitnessTestUpload(),
    responses={
        status.HTTP_200_OK: PostStudentExerciseResult(),
        status.HTTP_404_NOT_FOUND: NotFoundSerializer(),
        status.HTTP_400_BAD_REQUEST: ErrorSerializer(),
    },
)
@api_view(["POST"])
@permission_classes([IsTrainer | IsSuperUser])
def post_student_exercises_result(request, session_id=None, **kwargs):
    trainer = request.user
    if not trainer.is_superuser and not trainer.has_perm('sport.change_fitness_test'):
        return Response(
            status=status.HTTP_400_BAD_REQUEST,
        )
    serializer = FitnessTestUpload(data=request.data)
    serializer.is_valid(raise_exception=True)

    # If session_id is provided, get semester from existing session
    if session_id and session_id != 'new':
        try:
            existing_session = FitnessTestSession.objects.get(id=session_id)
            semester = existing_session.semester
        except FitnessTestSession.DoesNotExist:
            return Response(
                status=status.HTTP_404_NOT_FOUND,
                data=NotFoundSerializer({'detail': f'No fitness test session with id={session_id}'}).data
            )
    else:
        # For new sessions, get semester from request body
        semester_id = serializer.validated_data['semester_id']
        try:
            semester = Semester.objects.get(id=semester_id)
        except Semester.DoesNotExist:
            return Response(
                status=status.HTTP_404_NOT_FOUND,
                data=NotFoundSerializer({'detail': f'No semester with id={semester_id}'}).data
            )

    retake = serializer.validated_data['retake']
    results = serializer.validated_data['results']
    
    # Log the data for debugging
    logger.info(f"Fitness test upload request - session_id: {session_id}, semester: {semester}, retake: {retake}")
    logger.info(f"Results data: {results}")
    
    try:
        session = post_student_exercises_result_crud(semester, retake, results, session_id, request.user)
    except ValueError as e:
        logger.error(f"Error in fitness test upload: {e}")
        return Response(
            status=status.HTTP_400_BAD_REQUEST,
            data=ErrorSerializer({'detail': str(e)}).data
        )
    
    return Response(PostStudentExerciseResult({'session_id': session}).data)


# TODO: Rewrite suggest to JSON
@extend_schema(
    methods=["GET"],
    tags=["Fitness Test"],
    summary="Suggest students for fitness test",
    description="Suggest students based on a search term for fitness test. Only accessible by trainers.",
    parameters=[SuggestionQueryFTSerializer],
    responses={
        status.HTTP_200_OK: SuggestionSerializer(many=True),
    }
)
@api_view(["GET"])
@permission_classes([IsTrainer | IsSuperUser])
def suggest_fitness_test_student(request, **kwargs):
    serializer = SuggestionQueryFTSerializer(data=request.GET)
    serializer.is_valid(raise_exception=True)

    suggested_students = get_email_name_like_students(
        serializer.validated_data["term"],
        requirement=(~Q(fitnesstestresult__exercise__semester=get_current_semester_crud()))
    )
    return Response([
        {
            "value": f"{student['id']}_"
                     f"{student['full_name']}_"
                     f"{student['email']}_"
                     f"{student['medical_group__name']}_"
                     f"{student['gender']}",
            "label": f"{student['full_name']} "
                     f"({student['email']})",
        }
        for student in suggested_students
    ])
