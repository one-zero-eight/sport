from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('sport', '0134_add_is_paid_to_group'),
    ]

    operations = [
        migrations.CreateModel(
            name='TrainingReminder',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('sent_at', models.DateTimeField(auto_now_add=True)),
                ('training', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='reminders',
                    to='sport.training',
                )),
                ('student', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='reminders',
                    to='sport.student',
                )),
            ],
            options={
                'verbose_name': 'training reminder',
                'verbose_name_plural': 'training reminders',
                'db_table': 'training_reminder',
            },
        ),
        migrations.AddConstraint(
            model_name='trainingreminder',
            constraint=models.UniqueConstraint(
                fields=['training', 'student'],
                name='unique_training_reminder_per_student',
            ),
        ),
    ]
