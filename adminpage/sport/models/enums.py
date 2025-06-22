from django.db import models


class MedicalGroups(models.IntegerChoices):
    """
    NO_CHECKUP, SPECIAL2 - can't attend any trainings
    SPECIAL1 - can attend special groups
    PREPARATIVE, GENERAL - can attend everything
    """
    NO_CHECKUP = -2, "Medical checkup not passed"
    SPECIAL2 = -1, "Special 2"
    SPECIAL1 = 0, "Special 1"
    PREPARATIVE = 1, "Preparative"
    GENERAL = 2, "General"


class StudentStatuses(models.IntegerChoices):
    NORMAL = 0, "normal"
    DROPPED = 1, "dropped"
    ACADEMIC_LEAVE = 2, "academic leave"
    ALUMNUS = 3, "alumnus"


class Gender(models.IntegerChoices):
    UNKNOWN = -1, "unknown"
    MALE = 0, "male"
    FEMALE = 1, "female"


class GroupQR(models.IntegerChoices):
    NOT_MATTER = -1, "Does not matter"
    NO = 0, "No"
    YES = 1, "Yes"


class GenderInFTGrading(models.IntegerChoices):
    BOTH = -1, "both"
    MALE = 0, "male"
    FEMALE = 1, "female"