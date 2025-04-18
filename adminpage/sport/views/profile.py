import datetime

from django import forms
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from rest_framework.decorators import permission_classes

from api.crud import get_ongoing_semester, get_student_groups, \
    get_brief_hours, \
    get_trainer_groups, get_negative_hours, get_student_hours, get_faq, get_sports
from api.permissions import IsStudent
from sport.models import Student, MedicalGroupReference, Debt
from sport.utils import set_session_notification


class MedicalGroupReferenceForm(forms.Form):
    reference = forms.ImageField()
    student_comment = forms.CharField(
        widget=forms.Textarea,
        max_length=1024,
        label="Comments (optional)",
        required=False,
        empty_value='-'
    )


@login_required
def profile_view(request, **kwargs):
    user = request.user

    student = Student.objects.filter(pk=user.pk).select_related(
        "medical_group"
    ).first()  # type: Optional[Student]
    trainer = getattr(user, "trainer", None)  # type: Optional[Trainer]

    current_semester = get_ongoing_semester()
    sports = get_sports(student=student)

    context = {
        "now": datetime.datetime.now(tz=datetime.timezone.utc),
        "user": request.user,
        "common": {
            "semester_name": current_semester.name
        },
        "forms": {
            "medical_group_reference": MedicalGroupReferenceForm()
        },
        "sports": sports,  # TODO Check correctness
    }

    if "notify" in request.session:
        msg_type, msg = request.session["notify"]
        context.update({
            "notify": {
                "msg": msg,
                "type": msg_type,
            }
        })
        del request.session["notify"]

    if student is not None:
        student_groups = get_student_groups(student)
        student_groups_parsed = student_groups
        student_brief_hours_info = get_brief_hours(student)
        student_data = student.__dict__
        has_med_group_submission = MedicalGroupReference.objects.filter(
            student=student,
            semester=current_semester,
        ).exists()
        student_debt = Debt.objects.filter(
            student=student, semester=get_ongoing_semester())

        has_unresolved_med_group_submission = MedicalGroupReference.objects.filter(
            student=student,
            semester=current_semester,
            resolved=None,
        ).exists()
        ongoing_semester = get_student_hours(student.pk)['ongoing_semester']
        context.update({
            "student": {
                "student_id": student.pk,
                "sport_groups": student_groups_parsed,
                "group_choices_left": max(
                    0,
                    settings.STUDENT_MAXIMUM_GROUP_COUNT - len(
                        student_groups_parsed
                    )
                ),
                "semesters": student_brief_hours_info,
                "obj": student,
                "has_med_group_submission": has_med_group_submission,
                "has_unresolved_med_group_submission": has_unresolved_med_group_submission,
                **student_data,
                "sport": student.sport,
                "init_debt_hours": student_debt.first().debt if student_debt.exists() else 0,
                "debt_hours": get_negative_hours(student.pk),
                "all_hours": ongoing_semester,
                "earned_hours": int(ongoing_semester["hours_not_self"] + ongoing_semester["hours_self_not_debt"] + ongoing_semester["hours_self_debt"]),
            },
            "faq": get_faq(),
        })

    if trainer is not None:
        training_groups = get_trainer_groups(trainer)
        trainer_data = trainer.__dict__
        context.update({
            "trainer": {
                "sport_groups": training_groups,
                "obj": trainer,
                **trainer_data,
            },
        })

    return render(request, "profile.html", context)


@permission_classes([IsStudent])
def process_med_group_form(request, *args, **kwargs):
    form = MedicalGroupReferenceForm(request.POST, request.FILES)
    if form.is_valid():
        MedicalGroupReference.objects.create(
            student_id=request.user.pk,
            semester=get_ongoing_semester(),
            image=form.cleaned_data["reference"],
            student_comment=form.cleaned_data['student_comment']
        )

        set_session_notification(
            request,
            "Medical group reference has been successfully uploaded!",
            "success",
        )
        return redirect('profile')

    else:
        set_session_notification(request, "Form is invalid", "error")
    return redirect('profile')
