# Generated by Django 3.0.7 on 2020-07-03 13:49

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('sport', '0031_merge_20200703_1627'),
    ]

    operations = [
        migrations.CreateModel(
            name='MedicalGroup',
            fields=[
                ('id', models.IntegerField(primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=50)),
                ('description', models.TextField(max_length=1000)),
            ],
            options={
                'verbose_name_plural': 'medical groups',
                'db_table': 'medical_group',
            },
        ),
        migrations.RunSQL('''
        INSERT INTO medical_group (id, name, description) VALUES 
        (-2, 'Medical checkup not passed', 'You can''t get sport hours for training unless you pass a checkup'),
        (-1, 'Special 2', 'You can''t attend trainings, instead you should write a report on sport related topic'),
        (0, 'Special 1', 'Your health status is considered to be OK, you can attend any trainings'),
        (1, 'Preparative', 'Your health status is considered to be OK, you can attend any trainings'),
        (2, 'General', 'Your health status is considered to be OK, you can attend any trainings');
        ''', '')
    ]
