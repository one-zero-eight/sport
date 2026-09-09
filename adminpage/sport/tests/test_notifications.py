from datetime import datetime, timezone
from types import SimpleNamespace

from django.core import mail

from sport.signals import schedule
from sport.utils import notify_students


class StudentRecipients:
    def __init__(self, emails):
        self.emails = emails

    def values_list(self, *args, **kwargs):
        assert args == ("user__email",)
        assert kwargs == {"flat": True}
        return self

    def distinct(self):
        return self.emails


def test_notify_students_sends_one_email_to_hidden_recipients(settings):
    settings.EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"
    settings.DEFAULT_FROM_EMAIL = "sport@example.com"
    recipients = ["student1@example.com", "student2@example.com"]

    notify_students(
        StudentRecipients(recipients),
        "Training cancelled",
        "The {group_name} training was cancelled.",
        group_name="Football",
    )

    assert len(mail.outbox) == 1
    assert mail.outbox[0].to == []
    assert mail.outbox[0].bcc == recipients
    assert mail.outbox[0].body == "The Football training was cancelled."
    assert mail.outbox[0].alternatives[0].content == "The Football training was cancelled."
    assert mail.outbox[0].alternatives[0].mimetype == "text/html"


def test_notify_students_skips_email_without_recipients(settings):
    settings.EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"

    notify_students(StudentRecipients([]), "Subject", "Message")

    assert mail.outbox == []


def test_removed_training_uses_bulk_notification(monkeypatch):
    checkins = object()
    students = object()
    instance = SimpleNamespace(
        checkins=SimpleNamespace(all=lambda: checkins),
        checked_in_students=students,
        group=SimpleNamespace(to_frontend_name=lambda: "Football"),
        start=datetime(2026, 9, 9, 15, tzinfo=timezone.utc),
    )
    history_calls = []
    notification_calls = []
    monkeypatch.setattr(
        schedule.CheckoutHistory,
        "bulk_from_checkins",
        lambda *args: history_calls.append(args),
    )
    monkeypatch.setattr(
        schedule,
        "notify_students",
        lambda *args, **kwargs: notification_calls.append((args, kwargs)),
    )

    schedule.notify_about_removed_training(instance)

    assert history_calls == [
        (checkins, schedule.CheckoutHistory.Reason.TRAINING_CANCELLED)
    ]
    assert len(notification_calls) == 1
    args, kwargs = notification_calls[0]
    assert args == (students, *schedule.settings.EMAIL_TEMPLATES["training_deleted"])
    assert kwargs == {"group_name": "Football", "time": "09.09.2026 18:00"}
