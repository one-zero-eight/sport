# Generated by Django 3.1.8 on 2022-05-22 19:24

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('sport', '0108_trainingcheckin_attendance'),
    ]

    operations = [
        migrations.AddConstraint(
            model_name='trainingcheckin',
            constraint=models.UniqueConstraint(fields=('student', 'training'), name='student_training_checkin'),
        ),
    ]
