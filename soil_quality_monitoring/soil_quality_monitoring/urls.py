from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include
from django.views.generic import TemplateView

from farm_monitoring.views import crops, api

urlpatterns = [
    path('', TemplateView.as_view(template_name='index.html')),
    # Crops urls
    path('crops/', crops.CropListView.as_view()),
    # Measurements urls
    path('api/sensors', api.get_active_sensors, name='get_sensors'),
    path('api/measurement', api.add_measurement, name='api_add_measurement'),
    path('admin/', admin.site.urls),
]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
