from django.db import migrations, models


def clear_geometry_dependent_data(apps, schema_editor):
    Sensor = apps.get_model('farm_monitoring', 'Sensor')
    Sector = apps.get_model('farm_monitoring', 'Sector')
    Sensor.objects.all().delete()
    Sector.objects.all().delete()


class Migration(migrations.Migration):

    atomic = False

    dependencies = [
        ('farm_monitoring', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(clear_geometry_dependent_data, reverse_code=migrations.RunPython.noop),
        migrations.RemoveField(
            model_name='sector',
            name='x_start',
        ),
        migrations.RemoveField(
            model_name='sector',
            name='y_start',
        ),
        migrations.RemoveField(
            model_name='sector',
            name='width',
        ),
        migrations.RemoveField(
            model_name='sector',
            name='height',
        ),
        migrations.AddField(
            model_name='sector',
            name='polygon_coords',
            field=models.JSONField(
                default=list,
                help_text='Список точок [[x, y], ...] у відсотках 0–100 від canvas',
                verbose_name='Координати полігону',
            ),
            preserve_default=False,
        ),
    ]
