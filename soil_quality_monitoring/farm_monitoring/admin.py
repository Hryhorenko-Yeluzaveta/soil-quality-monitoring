from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from farm_monitoring.models import Crop, Sector, Sensor, Measurement, User


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


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'first_name', 'last_name', 'role', 'is_active')
    list_filter = ('role', 'is_active')

    fieldsets = UserAdmin.fieldsets + (
        ('Роль та доступи', {'fields': ('role',)}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Роль та доступи', {'fields': ('role',)}),
    )