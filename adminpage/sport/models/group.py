from django.db import models
from django.db.models import Q

from sport.models.enums import GroupQR, GenderInFTGrading
from sport.utils import str_or_empty


class Group(models.Model):
    semester = models.ForeignKey('Semester', on_delete=models.CASCADE, null=False)
    sport = models.ForeignKey('Sport', on_delete=models.CASCADE, null=True, blank=True)
    name = models.CharField(max_length=50, blank=True, null=True)
    capacity = models.PositiveIntegerField(default=20, null=False)
    is_club = models.BooleanField(default=False, null=False)
    trainer = models.ForeignKey('Trainer', on_delete=models.SET_NULL, null=True, blank=True, verbose_name='teacher')
    trainers = models.ManyToManyField('Trainer', related_name='m2m', blank=True, verbose_name='teachers')
    accredited = models.BooleanField(default=True, null=False)

    # minimum_medical_group = models.ForeignKey('MedicalGroup', on_delete=models.DO_NOTHING, null=True, blank=True)
    allowed_medical_groups = models.ManyToManyField(
        'MedicalGroup',
        blank=True,
        help_text='Select medical groups required to attend the trainings. If this is empty, nobody will see the training (except students in "Allowed students" list, they always see the training).'
    )
    allowed_gender = models.IntegerField(
        choices=GenderInFTGrading.choices,
        default=GenderInFTGrading.BOTH,
        help_text='Select genders that are allowed to attend the trainings (works with "Allowed medical groups" filter).'
    )
    allowed_qr = models.IntegerField(
        choices=GroupQR.choices,
        default=-1,
        verbose_name="Is a QR required?"
    )
    allowed_students = models.ManyToManyField(
        'Student',
        related_name='allowed_groups',
        blank=True,
        help_text='List of students that are allowed to attend classes (in addition to "Allowed medical groups" filter).'
    )
    banned_students = models.ManyToManyField(
        'Student',
        related_name='banned_groups',
        blank=True,
        help_text='List of students that can not attend classes. The students will not see the training, and the teacher will not be able to set hours for these students.'
    )

    class Meta:
        db_table = "group"
        verbose_name_plural = "groups"
        constraints = [
            models.CheckConstraint(check=Q(Q(sport__isnull=False) | (Q(name__isnull=False) & (~Q(name__exact="")))),
                                   name='sport_or_name'),
        ]
        indexes = [
            models.Index(fields=("name",)),
        ]

    def to_frontend_name(self):
        return f"{str_or_empty(self.sport)}{' - ' if self.sport and self.name else ''}{str_or_empty(self.name)}"

    def __str__(self):
        return f"[{self.semester}] {str_or_empty(self.sport)}{' - ' if self.sport and self.name else ''}{str_or_empty(self.name)}"
