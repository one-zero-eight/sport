# Generated by Django 3.0.7 on 2021-01-16 16:24

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('sport', '0048_merge_20210116_1924'),
    ]

    operations = [
        migrations.AddField(
            model_name='selfsportreport',
            name='comment',
            field=models.TextField(blank=True, max_length=1024, null=True),
        ),
    ]