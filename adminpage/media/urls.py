from django.conf import settings
from django.urls import path

from media.views import (
    medical_reference_download,
    self_sport_download,
    medical_group_reference_download,
)

urlpatterns = [
    # media download
    path(f"{settings.MEDICAL_REFERENCE_FOLDER}/<str:semester_name>/"
         f"<int:student_id>/<str:filename>", medical_reference_download),

    path(f"{settings.SELF_SPORT_FOLDER}/<str:semester_name>/"
         f"<int:student_id>/<str:filename>", self_sport_download),

    path(f"{settings.MEDICAL_GROUP_REFERENCE_FOLDER}/"
         f"<int:student_id>/<str:filename>", medical_group_reference_download),
]
