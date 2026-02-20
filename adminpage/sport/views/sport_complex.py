import datetime

from django.forms.utils import to_current_timezone
from django.shortcuts import render, redirect

from adminpage.settings import SPORT_COMPLEX_EMAIL
from sport.models import Training


def sport_complex_view(request, **kwargs):
    if not (request.user.is_authenticated and (request.user.is_staff or getattr(request.user, "email", None) == SPORT_COMPLEX_EMAIL)):
        return redirect("/admin/login/?next=/sport-complex/")

    now = datetime.datetime.now(tz=datetime.timezone.utc)
    today_end = datetime.datetime(now.year, now.month, now.day, 23, 59, 59, tzinfo=datetime.timezone.utc)

    today_trainings = (
        Training.objects.filter(
            start__lte=today_end,  # Starts today
            end__gte=now,  # And not finished yet
        )
        .order_by("start")
        .select_related(
            "group",
            "group__sport",
            "training_class",
        )
        .prefetch_related(
            "group__trainers__user",
            "checkins__student__user",
            "group__always_allow_students__user",
        )
    )

    today_schedule_with_checkins = [
        {
            "training_id": training.id,
            "title": training.group.to_frontend_name(),
            "location": training.training_class.name,
            "formatted_timerange": f"{to_current_timezone(training.start).time().strftime('%H:%M')}-{to_current_timezone(training.end).time().strftime('%H:%M')}",
            "trainers": sorted([
                f"{trainer.user.get_full_name()} ({trainer.user.email})" for trainer in training.group.trainers.all()
            ]),
            "always_allow": sorted([
                f"{student.user.get_full_name()} ({student.user.email})" for student in
                training.group.always_allow_students.all()
            ]),
            "checkins": sorted([
                f"{checkin.student.user.get_full_name()} ({checkin.student.user.email})" for checkin in training.checkins.all()
            ]),
        }
        for training in today_trainings
    ]

    return render(
        request,
        "sport_complex.html",
        context={
            "formatted_now": to_current_timezone(now).strftime("%Y-%m-%d %H:%M:%S"),
            "today_schedule_with_checkins": today_schedule_with_checkins,
        }
    )
