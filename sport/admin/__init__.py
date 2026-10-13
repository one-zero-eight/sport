# ruff: noqa: E402

from django.contrib import admin

# add save button on top for all admins
admin.ModelAdmin.save_on_top = True

from .admin_site import SportAdminSite as SportAdminSite
from .admin_site import site as site
from .attendance_admin import AttendanceAdmin as AttendanceAdmin
from .course_admin import CourseAdmin as CourseAdmin
from .debt_admin import DebtAdmin as DebtAdmin
from .django_group_admin import DjangoGroupAdmin as DjangoGroupAdmin
from .faq_admin import FAQAdmin as FAQAdmin
from .fitness_test_exercise_admin import FitnessTestExerciseAdmin as FitnessTestExerciseAdmin
from .fitness_test_grading_admin import FitnessTestGradingAdmin as FitnessTestGradingAdmin
from .fitness_test_result_admin import FitnessTestResultAdmin as FitnessTestResultAdmin
from .fitness_test_session_admin import FitnessTestSessionAdmin as FitnessTestSessionAdmin
from .group_admin import GroupAdmin as GroupAdmin
from .measurement_admin import Measurement as Measurement
from .measurement_result_admin import MeasurementResult as MeasurementResult
from .measurement_session_admin import MeasurementSession as MeasurementSession
from .medical_group_admin import MedicalGroupAdmin as MedicalGroupAdmin
from .medical_group_history_admin import MedicalGroupHistoryAdmin as MedicalGroupHistoryAdmin
from .medical_group_reference_admin import MedicalGroupReferenceAdmin as MedicalGroupReferenceAdmin
from .reference_admin import ReferenceAdmin as ReferenceAdmin
from .schedule_admin import ScheduleAdmin as ScheduleAdmin
from .self_sport_admin import SelfSportAdmin as SelfSportAdmin
from .self_sport_type_admin import SelfSportTypeAdmin as SelfSportTypeAdmin
from .semester_admin import SemesterAdmin as SemesterAdmin
from .sport_admin import SportAdmin as SportAdmin
from .student_admin import StudentAdmin as StudentAdmin
from .student_status_admin import StudentStatusAdmin as StudentStatusAdmin
from .trainer_admin import TrainerAdmin as TrainerAdmin
from .training_admin import TrainingAdmin as TrainingAdmin
from .training_check_in_admin import TrainingCheckInAdmin as TrainingCheckInAdmin
from .training_class_admin import TrainingClassAdmin as TrainingClassAdmin
from .user_admin import UserAdmin as UserAdmin
