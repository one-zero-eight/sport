# Generated by Django 3.1.8 on 2021-07-10 07:10

from django.db import migrations, models
import sport.models.student


class Migration(migrations.Migration):

    dependencies = [
        ('sport', '0055_student_is_online'),
    ]

    operations = [
        migrations.AddField(
            model_name='student',
            name='course',
            field=models.PositiveSmallIntegerField(default=1, validators=[sport.models.student.validate_course]),
        ),
    ]
