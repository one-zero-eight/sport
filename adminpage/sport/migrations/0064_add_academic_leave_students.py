# Generated by Django 3.1.8 on 2021-08-01 16:01

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('sport', '0063_add_student_academic_leave_to_semester'),
    ]

    operations = [
        migrations.AlterField(
            model_name='semester',
            name='academic_leave_students',
            field=models.ManyToManyField(blank=True, to='sport.Student'),
        ),
    ]