from django.contrib import admin

from .attendanceAdmin import AttendanceAdmin as AttendanceAdmin
from .courseAdmin import CourseAdmin as CourseAdmin
from .debtAdmin import DebtAdmin as DebtAdmin
from .djangoGroupAdmin import DjangoGroupAdmin as DjangoGroupAdmin
from .FAQAdmin import FAQAdmin as FAQAdmin
from .fitnessTestExerciseAdmin import FitnessTestExerciseAdmin as FitnessTestExerciseAdmin
from .fitnessTestGradingAdmin import FitnessTestGradingAdmin as FitnessTestGradingAdmin
from .fitnessTestResultAdmin import FitnessTestResultAdmin as FitnessTestResultAdmin
from .fitnessTestSessionAdmin import FitnessTestSessionAdmin as FitnessTestSessionAdmin
from .groupAdmin import GroupAdmin as GroupAdmin
from .measurementAdmin import Measurement as Measurement
from .measurementResultAdmin import MeasurementResult as MeasurementResult
from .measurementSessionAdmin import MeasurementSession as MeasurementSession
from .medicalGroupAdmin import MedicalGroupAdmin as MedicalGroupAdmin
from .medicalGroupHistoryAdmin import MedicalGroupHistoryAdmin as MedicalGroupHistoryAdmin
from .medicalGroupReferenceAdmin import MedicalGroupReferenceAdmin as MedicalGroupReferenceAdmin
from .referenceAdmin import ReferenceAdmin as ReferenceAdmin
from .scheduleAdmin import ScheduleAdmin as ScheduleAdmin
from .selfSportAdmin import SelfSportAdmin as SelfSportAdmin
from .selfsportTypeAdmin import SelfSportTypeAdmin as SelfSportTypeAdmin
from .semesterAdmin import SemesterAdmin as SemesterAdmin
from .site import SportAdminSite as SportAdminSite
from .site import site as site
from .sportAdmin import SportAdmin as SportAdmin
from .studentAdmin import StudentAdmin as StudentAdmin
from .studentStatusAdmin import StudentStatusAdmin as StudentStatusAdmin
from .trainerAdmin import TrainerAdmin as TrainerAdmin
from .trainingAdmin import TrainingAdmin as TrainingAdmin
from .trainingCheckInAdmin import TrainingCheckInAdmin as TrainingCheckInAdmin
from .trainingClassAdmin import TrainingClassAdmin as TrainingClassAdmin
from .userAdmin import UserAdmin as UserAdmin

# add save button on top for all admins
admin.ModelAdmin.save_on_top = True
