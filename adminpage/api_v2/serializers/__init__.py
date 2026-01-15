from .attendance import (
    SuggestionQuerySerializer,
    SuggestionSerializer,
    StudentInfoSerializer,
    GradeReportSerializer,
    TrainingGradesSerializer,
    LastAttendedStat,
    LastAttendedDatesSerializer,
    BadGradeReportGradeSerializer,
    BadGradeReport,
    AttendanceMarkSerializer,
    HoursInfoSerializer,
    HoursInfoFullSerializer,
    AttendanceSerializer,
    StudentHoursSummarySerializer,
    SemesterHoursSummarySerializer,
    GradesCsvRowSerializer,
)
from .calendar import (
    CalendarRequestSerializer,
    ScheduleExtendedPropsSerializer,
    CalendarSerializer,
    CalendarPersonalSerializer,
    CalendarSportSerializer,
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
    SportSerializer,
    SportsSerializer,
    GroupInfoSerializer,
)
from .profile import (
    TrainingHourSerializer,
)
from .reference import (
    ReferenceUploadSerializer,
    ReferenceUploadResponseSerializer,
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
    TrainingCheckInRequest,
)

from .student import (
    # StudentSerializer,
    UserSerializer,
)
