# Generated by Django 3.1.8 on 2021-07-20 16:52

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('sport', '0057_permissions'),
    ]

    operations = [
        migrations.AddField(
            model_name='semester',
            name='hours',
            field=models.IntegerField(default=30),
        ),
    ]
