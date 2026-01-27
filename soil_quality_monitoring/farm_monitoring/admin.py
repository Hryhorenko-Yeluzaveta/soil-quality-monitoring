from django.contrib import admin
from farm_monitoring.models import Crop, Sector, Sensor, Measurement


@admin.register(Crop)
class CropAdmin(admin.ModelAdmin):
    pass

@admin.register(Sector)
class SectorAdmin(admin.ModelAdmin):
    pass

@admin.register(Sensor)
class SensorAdmin(admin.ModelAdmin):
    pass

@admin.register(Measurement)
class MeasurementAdmin(admin.ModelAdmin):
    pass