# Generated by Django 5.1.3 on 2025-01-14 18:30

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('sport', '0124_group_allowed_students'),
    ]

    operations = [
        migrations.AlterField(
            model_name='group',
            name='allowed_students',
            field=models.ManyToManyField(blank=True, related_name='allowed_groups', to='sport.student'),
        ),
    ]
