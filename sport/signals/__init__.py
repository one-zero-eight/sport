from .reference import update_hours_for_reference as update_hours_for_reference
from .schedule import (
    create_trainings_current_semester as create_trainings_current_semester,
)
from .schedule import (
    remove_future_trainings_from_schedule as remove_future_trainings_from_schedule,
)
from .self_sport_report import create_attendance_record as create_attendance_record
from .semester import (
    get_or_create_college_group as get_or_create_college_group,
)
from .semester import (
    get_or_create_student_group as get_or_create_student_group,
)
from .semester import (
    get_or_create_trainer_group as get_or_create_trainer_group,
)
from .semester import (
    increase_course as increase_course,
)
from .semester import (
    nullify_medical_groups as nullify_medical_groups,
)
from .semester import (
    special_groups_create as special_groups_create,
)
from .user import change_status_to_academic_leave as change_status_to_academic_leave
from .user import create_student_profile as create_student_profile
from .user import verify_bachelor_role as verify_bachelor_role
