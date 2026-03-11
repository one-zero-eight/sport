from datetime import datetime, time, timedelta

from django.conf import settings
from django.core.management.base import BaseCommand
from django.forms.utils import to_current_timezone
from django.utils import timezone

from sport.models import Training, TrainingReminder


class Command(BaseCommand):
    help = (
        "Send training reminder emails to checked-in students. "
        "Run at 08:00 to remind about evening trainings (start >= 12:00) today. "
        "Run at 20:00 to remind about morning trainings (start < 12:00) tomorrow. "
        "Students who check in after a previous run will receive a reminder on the next run."
    )

    def handle(self, *args, **options):
        now = timezone.localtime()
        today = now.date()
        local_tz = timezone.get_current_timezone()

        if 6 <= now.hour < 12:
            window_start = timezone.make_aware(
                datetime.combine(today, time(12, 0)), local_tz
            )
            window_end = timezone.make_aware(
                datetime.combine(today + timedelta(days=1), time(0, 0)), local_tz
            )
            self.stdout.write("Morning run: reminding about evening trainings today")
        elif 18 <= now.hour < 24:
            tomorrow = today + timedelta(days=1)
            window_start = timezone.make_aware(
                datetime.combine(tomorrow, time(0, 0)), local_tz
            )
            window_end = timezone.make_aware(
                datetime.combine(tomorrow, time(12, 0)), local_tz
            )
            self.stdout.write("Evening run: reminding about morning trainings tomorrow")
        else:
            self.stdout.write("Outside reminder windows (06-12 and 18-24), nothing to do.")
            return

        trainings = Training.objects.filter(
            start__gte=window_start, start__lt=window_end
        ).select_related("group", "training_class")

        already_reminded = set(
            TrainingReminder.objects.filter(training__in=trainings).values_list(
                "training_id", "student_id"
            )
        )

        subject, message = settings.EMAIL_TEMPLATES["training_reminder"]
        reminders_to_create = []
        sent_count = 0

        for training in trainings:
            students = [
                s for s in training.checked_in_students
                if (training.pk, s.pk) not in already_reminded
            ]
            if not students:
                continue

            local_start = to_current_timezone(training.start)
            local_end = to_current_timezone(training.end)
            location = training.training_class.name if training.training_class else "—"

            for student in students:
                student.notify(
                    subject,
                    message,
                    student_name=student.user.first_name,
                    group_name=training.group.to_frontend_name(),
                    date=local_start.strftime("%d.%m.%Y"),
                    start_time=local_start.strftime("%H:%M"),
                    end_time=local_end.strftime("%H:%M"),
                    location=location,
                )
                reminders_to_create.append(
                    TrainingReminder(training=training, student=student)
                )
                sent_count += 1

        TrainingReminder.objects.bulk_create(reminders_to_create, ignore_conflicts=True)

        self.stdout.write(
            self.style.SUCCESS(f"Done: sent {sent_count} reminder emails.")
        )
