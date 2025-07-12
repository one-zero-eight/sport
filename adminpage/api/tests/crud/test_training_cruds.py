import pytest
import unittest
from datetime import date, time, datetime

from api.crud import enroll_student, \
    get_group_info, \
    get_trainings_for_student, get_trainings_for_trainer, get_students_grades
from sport.models import Training, Schedule

testcase = unittest.TestCase()
testcase.maxDiff = None
assertMembers = testcase.assertCountEqual


# @pytest.mark.django_db
# @pytest.mark.freeze_time('2019-12-31 10:00')
# def test_training_info(student_factory, trainer_factory, sport_factory,
#                        semester_factory, training_class_factory,
#                        group_factory,
#                        schedule_factory,
#                        attendance_factory):
#     student = student_factory("A1@foo.bar").student
#     other_student = student_factory("A2@foo.bar").student
#     trainer = trainer_factory("B@foo.bar").trainer
#     sport = sport_factory(name="Sport")
#     semester = semester_factory(
#         name="S19",
#         start=date(2020, 1, 1),
#         end=date(2020, 1, 30)
#     )
#     training_class = training_class_factory(name="1337")
#     group = group_factory(
#         name="G1",
#         sport=sport,
#         semester=semester,
#         capacity=20,
#     )
#     group.trainers.add(trainer)
#     schedule = schedule_factory(
#         group=group,
#         weekday=Schedule.Weekday.MONDAY,
#         start=time(14, 0, 0),
#         end=time(18, 30, 0),
#         training_class=training_class
#     )
#
#     trainings = Training.objects.all()
#     t1 = trainings[0]
#     t2 = trainings[1]
#     t2.training_class = None
#     t2.save()
#     a1 = attendance_factory(training=t1, student=student, hours=1)
#     assert get_attended_training_info(t1.pk, student) == {
#         "group_id": group.pk,
#         "group_name": group.name,
#         "custom_name": None,
#         "link": None,
#         "link_name": None,
#         "group_description": group.description,
#         "training_class": training_class.name,
#         "capacity": group.capacity,
#         "current_load": 0,
#         'trainer_email': None,
#         'trainer_first_name': None,
#         'trainer_last_name': None,
#         'trainers': [{
#             "trainer_first_name": trainer.user.first_name,
#             "trainer_last_name": trainer.user.last_name,
#             "trainer_email": trainer.user.email
#         }],
#         "hours": a1.hours,
#         "is_enrolled": False,
#     }
#     assert get_group_info(group.pk, student) == {
#         "group_id": group.pk,
#         "group_name": group.name,
#         "group_description": group.description,
#         "link": None,
#         "link_name": None,
#         "capacity": group.capacity,
#         "current_load": 0,
#         'trainer_email': None,
#         'trainer_first_name': None,
#         'trainer_last_name': None,
#         'trainers': [{
#             "trainer_first_name": trainer.user.first_name,
#             "trainer_last_name": trainer.user.last_name,
#             "trainer_email": trainer.user.email
#         }],
#         "is_enrolled": False,
#         "can_enroll": False,
#         "is_club": False,
#     }
#     assert \
#         get_trainings_for_trainer(
#             trainer=trainer,
#             start=datetime(2020, 1, 1),
#             end=datetime(2020, 1, 14)
#         ) == \
#         [
#             {
#                 "id": t1.pk,
#                 "start": t1.start,
#                 "end": t1.end,
#                 "group_id": group.pk,
#                 "group_name": group.name,
#                 "training_class": training_class.name,
#                 "can_grade": True
#             },
#             {
#                 "id": t2.pk,
#                 "start": t2.start,
#                 "end": t2.end,
#                 "group_id": group.pk,
#                 "group_name": group.name,
#                 "training_class": None,
#                 "can_grade": True
#             }
#         ]
#
#     enroll_student(group, student)
#     group.trainers.clear()
#     group.save()
#     assert get_attended_training_info(t2.pk, student) == {
#         "group_id": group.pk,
#         "group_name": group.name,
#         "custom_name": None,
#         "link": None,
#         "link_name": None,
#         "group_description": group.description,
#         "training_class": None,
#         "capacity": group.capacity,
#         "current_load": 1,
#         'trainer_email': None,
#         'trainer_first_name': None,
#         'trainer_last_name': None,
#         'trainers': [],
#         "hours": 0,
#         "is_enrolled": True,
#     }
#     assert get_group_info(group.pk, student) == {
#         "group_id": group.pk,
#         "group_name": group.name,
#         "group_description": group.description,
#         "link": None,
#         "link_name": None,
#         "capacity": group.capacity,
#         "current_load": 1,
#         "trainer_first_name": None,
#         "trainer_last_name": None,
#         "trainer_email": None,
#         'trainers': [],
#         "is_enrolled": True,
#         'can_enroll': False,
#         "is_club": False,
#     }
#     assertMembers(
#         get_trainings_for_student(
#             student=student,
#             start=datetime(2020, 1, 1),
#             end=datetime(2020, 1, 14)
#         ),
#         [
#             {
#                 "id": t1.pk,
#                 "start": t1.start,
#                 "end": t1.end,
#                 "group_id": group.pk,
#                 "group_name": group.name,
#                 "training_class": training_class.name,
#                 "can_grade": False
#             },
#             {
#                 "id": t2.pk,
#                 "start": t2.start,
#                 "end": t2.end,
#                 "group_id": group.pk,
#                 "group_name": group.name,
#                 "training_class": None,
#                 "can_grade": False
#             }
#         ])
#
#     assert get_trainings_for_trainer(
#         trainer=trainer,
#         start=datetime(2020, 1, 1),
#         end=datetime(2020, 1, 14)
#     ) == []
#
#     assert get_students_grades(t1.pk) == [{
#         "student_id": student.pk,
#         "first_name": student.user.first_name,
#         "last_name": student.user.last_name,
#         "email": student.user.email,
#         "med_group": "Medical checkup not passed",
#         "hours": a1.hours,
#         "full_name": f"{student.user.first_name} {student.user.last_name}",
#     }]
#     assert get_students_grades(t2.pk) == [{
#         "student_id": student.pk,
#         "first_name": student.user.first_name,
#         "last_name": student.user.last_name,
#         "email": student.user.email,
#         "med_group": "Medical checkup not passed",
#         "hours": 0,
#         "full_name": f"{student.user.first_name} {student.user.last_name}",
#
#     }]
#
#     enroll_student(group, other_student)
#
#     assertMembers(get_students_grades(t1.pk), [
#         {
#             "student_id": student.pk,
#             "first_name": student.user.first_name,
#             "last_name": student.user.last_name,
#             "email": student.user.email,
#             "med_group": "Medical checkup not passed",
#             "hours": a1.hours,
#             "full_name": f"{student.user.first_name} {student.user.last_name}",
#         },
#         {
#             "student_id": other_student.pk,
#             "first_name": other_student.user.first_name,
#             "last_name": other_student.user.last_name,
#             "email": other_student.user.email,
#             "med_group": "Medical checkup not passed",
#             "hours": 0,
#             "full_name": f"{student.user.first_name} {student.user.last_name}",
#         }
#     ])
#
#     student.has_QR = True
#     student.save()
#     other_student.has_QR = True
#     other_student.save()
#
#     assert get_students_grades(t1.pk) == [{
#         "student_id": student.pk,
#         "first_name": student.user.first_name,
#         "last_name": student.user.last_name,
#         "email": student.user.email,
#         "med_group": "Medical checkup not passed",
#         "hours": a1.hours,
#         "full_name": f"{student.user.first_name} {student.user.last_name}",
#     }]
