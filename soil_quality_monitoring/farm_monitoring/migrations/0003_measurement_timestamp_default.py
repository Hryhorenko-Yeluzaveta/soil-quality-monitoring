from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('farm_monitoring', '0002_sector_polygon'),
    ]

    operations = [
        migrations.AlterField(
            model_name='measurement',
            name='timestamp',
            field=models.DateTimeField(default=django.utils.timezone.now),
        ),
    ]
