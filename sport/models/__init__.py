from django.contrib.auth.models import Group as DjangoGroup
from django.db import models

from .attendance import Attendance as Attendance
from .checkout_history import CheckoutHistory as CheckoutHistory
from .course import Course as Course
from .custom_permission import CustomPermission as CustomPermission
from .debt import Debt as Debt
from .enroll import Enroll as Enroll
from .enums import Gender as Gender
from .enums import MedicalGroups as MedicalGroups
from .enums import StudentStatuses as StudentStatuses
from .faq_category import FAQCategory as FAQCategory
from .faq_element import FAQElement as FAQElement
from .fitness_test_exercise import FitnessTestExercise as FitnessTestExercise
from .fitness_test_grading import FitnessTestGrading as FitnessTestGrading
from .fitness_test_result import FitnessTestResult as FitnessTestResult
from .fitness_test_session import FitnessTestSession as FitnessTestSession
from .group import Group as Group
from .measurement import Measurement as Measurement
from .measurement_result import MeasurementResult as MeasurementResult
from .measurement_session import MeasurementSession as MeasurementSession
from .medical_group import MedicalGroup as MedicalGroup
from .medical_group_history import MedicalGroupHistory as MedicalGroupHistory
from .medical_group_reference import MedicalGroupReference as MedicalGroupReference
from .medical_group_reference import MedicalGroupReferenceImage as MedicalGroupReferenceImage
from .reference import Reference as Reference
from .schedule import Schedule as Schedule
from .self_sport import SelfSportReport as SelfSportReport
from .self_sport_type import SelfSportType as SelfSportType
from .semester import Semester as Semester
from .sport import Sport as Sport
from .student import Student as Student
from .student import save_student_profile as save_student_profile
from .student_status import StudentStatus as StudentStatus
from .trainer import Trainer as Trainer
from .training import Training as Training
from .training_checkin import TrainingCheckIn as TrainingCheckIn
from .training_class import TrainingClass as TrainingClass
from .training_reminder import TrainingReminder as TrainingReminder

DjangoGroup.add_to_class(
    "verbose_name",
    models.CharField(
        max_length=180,
        null=True,
        blank=False,
        unique=True,
    ),
)

DjangoGroup.add_to_class("__str__", lambda self: str(self.verbose_name))

DjangoGroup.add_to_class("natural_key", lambda self: (str(self.verbose_name),))
