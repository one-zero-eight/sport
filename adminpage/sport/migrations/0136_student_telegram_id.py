from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('sport', '0135_trainingreminder'),
    ]

    operations = [
        migrations.AddField(
            model_name='student',
            name='telegram_id',
            field=models.BigIntegerField(blank=True, db_index=True, null=True),
        ),
    ]
