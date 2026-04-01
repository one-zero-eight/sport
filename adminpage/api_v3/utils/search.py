from django.db.models import Q, F, Value
from django.db.models.functions import Concat

from sport.models import Student


def search_students(pattern: str, limit: int = 5, requirement=None):
    if requirement is None:
        requirement = ~Q(pk=None)
    qs = (
        Student.objects.annotate(
            id=F("user__id"),
            first_name=F("user__first_name"),
            last_name=F("user__last_name"),
            email=F("user__email"),
            full_name=Concat("user__first_name", Value(" "), "user__last_name"),
        )
        .filter(requirement & (Q(email__icontains=pattern) | Q(full_name__icontains=pattern) | Q(last_name__icontains=pattern)))
        .values("id", "first_name", "last_name", "email", "medical_group__name")[:limit]
    )
    return [{**row, "medical_group": row.pop("medical_group__name")} for row in qs]
