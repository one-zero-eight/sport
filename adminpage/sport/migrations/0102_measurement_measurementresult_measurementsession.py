# Generated by Django 3.1.8 on 2022-05-02 12:49

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('sport', '0101_auto_20220301_0105'),
    ]

    operations = [
        migrations.CreateModel(
            name='Measurement',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(blank=True, max_length=1000, null=True)),
                ('value_unit', models.CharField(blank=True, max_length=1000, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='MeasurementSession',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date', models.DateTimeField()),
                ('approved', models.BooleanField(default=False)),
                ('semester', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='sport.semester')),
                ('student', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='sport.student')),
            ],
        ),
        migrations.CreateModel(
            name='MeasurementResult',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('value', models.IntegerField()),
                ('measurement', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='sport.measurement')),
                ('session', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='sport.measurementsession')),
            ],
        ),
    ]