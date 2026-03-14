from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.auth.views import LoginView, LogoutView
from django.urls import path, include
from django.views.generic import TemplateView

from farm_monitoring.views import crops, api, sensors, sectors
from farm_monitoring.views.sectors import api_realtime_measurements

urlpatterns = [
    path('', TemplateView.as_view(template_name='index.html'), name='index'),
    path('login/', LoginView.as_view(template_name='login.html', redirect_authenticated_user=True), name='login'),
    path('logout/', LogoutView.as_view(next_page='login'), name='logout'),
    path('dashboard/', sectors.SectorListView.as_view(), name="dashboard"),
    # Crops urls
    path('crops/', crops.CropListView.as_view(), name='crops'),
    path('crops/create', crops.CropCreateView.as_view()),
    path('crops/update/<int:pk>', crops.CropUpdateView.as_view(), name='crop_update'),
    path('crops/delete/<int:pk>', crops.CropDeleteView.as_view(), name='crop_delete'),
    # Sensors urls
    path('sensors/', sensors.SensorListView.as_view(), name='sensors'),
    path('sensors/create', sensors.SensorCreateView.as_view()),
    path('sensors/update/<int:pk>', sensors.SensorUpdateView.as_view(), name='sensor_update'),
    path('sensors/delete/<int:pk>', sensors.SensorDeleteView.as_view(), name='sensor_delete'),
    # Sector urls
    path('sectors/create', sectors.SectorCreateView.as_view(), name="sector_create"),
    path('sectors/update/<int:pk>', sectors.SectorUpdateView.as_view(), name="sector_update"),
    path('sectors/delete/<int:pk>', sectors.SectorDeleteView.as_view(), name="sector_delete"),
    # Measurements urls
    path('api/sensors', api.get_active_sensors, name='get_sensors'),
    path('api/measurement', api.add_measurement, name='api_add_measurement'),
    path('api/sectors/realtime/', api_realtime_measurements, name='api_realtime_sectors'),
    path('admin/', admin.site.urls),
]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
