import pytest

from sport.models import Debt, Student, StudentStatus, StudentStatuses


def assert_status_change_preserves_debt(student):
    debt = Debt.objects.create(student=student, debt=42)

    student.student_status = StudentStatus.objects.get(pk=StudentStatuses.DROPPED)
    student.save()
    assert student.user.groups.filter(name="STUDENT_STATUS_1").exists()

    student.student_status = StudentStatus.objects.get(pk=StudentStatuses.NORMAL)
    student.save()
    assert student.user.groups.filter(name="STUDENT_STATUS_0").exists()

    assert Student.objects.filter(pk=student.pk).exists()
    debt.refresh_from_db()
    assert debt.debt == 42


@pytest.mark.django_db
def test_changing_student_status_preserves_debt(student_factory):
    student = student_factory("student@example.com").student

    assert_status_change_preserves_debt(student)


@pytest.mark.django_db
def test_changing_legacy_student_status_preserves_debt(user_factory):
    user = user_factory("legacy-student@example.com")
    student = Student.objects.create(user=user)

    assert_status_change_preserves_debt(student)
