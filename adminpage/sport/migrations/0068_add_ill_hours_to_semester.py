# Generated by Django 3.1.8 on 2021-08-02 09:33

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('sport', '0067_add_studentcomment_start_end_to_reference'),
    ]

    operations = [
        migrations.AddField(
            model_name='semester',
            name='number_hours_one_day_ill',
            field=models.IntegerField(default=1),
        ),
    ]
