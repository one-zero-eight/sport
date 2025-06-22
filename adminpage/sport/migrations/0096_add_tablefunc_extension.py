from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('sport', '0095_auto_20211209_2132'),
    ]

    operations = [
        migrations.RunSQL(sql="CREATE EXTENSION tablefunc")
    ]
