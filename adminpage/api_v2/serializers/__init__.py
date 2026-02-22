from .faq import (
    FAQDictSerializer
)

from .attendance import (
    SuggestionQuerySerializer,
    SuggestionSerializer,
    TrainingGradesSerializer,
    BadGradeReportGradeSerializer,
    BadGradeReport,
    AttendanceMarkSerializer,
    StudentHoursSummarySerializer,
)
from .calendar import (
    CalendarRequestSerializer,
    CalendarPersonalSerializer,
)
from .common import (
    EmptySerializer,
    NotFoundSerializer,
    ErrorSerializer,
    InbuiltErrorSerializer,
    get_error_serializer,
    error_detail,
)

from .group import (
    ScheduleSerializer,
    GroupInfoSerializer,
)

from .reference import (
    ReferenceUploadSerializer,
    ReferenceUploadResponseSerializer,
    MedicalGroupReferenceUploadSerializer,
    MedicalGroupReferenceUploadResponseSerializer
)
from .self_sport_report import (
    SelfSportReportUploadSerializer,
)
from .training import (
    TrainingInfoSerializer,
)
from .fitness_test import (
    FitnessTestResultSerializer,
    FitnessTestResults
)

from .medical_groups import (
    MedicalGroupSerializer,
)

from .training_classes import (
    TrainingClassesSerializer,
)

from .student import (
    UserSerializer,
)
