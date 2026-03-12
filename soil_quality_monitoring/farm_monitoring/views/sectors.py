from django.db.models import OuterRef, Subquery, Prefetch
from django.http import HttpResponseRedirect, JsonResponse
from django.urls import reverse_lazy
from django.views.generic import CreateView, UpdateView, ListView, DeleteView

from farm_monitoring.forms import SectorCreateForm, SectorUpdateForm
from farm_monitoring.models import Sector, Measurement, Sensor


def get_annotated_sectors():
    latest_measurement_subquery = Measurement.objects.filter(
        sensor=OuterRef('pk')
    ).order_by('-timestamp').values('value')[:1]

    active_sensors_with_latest_data = Sensor.objects.filter(
        is_active=True,
        archived=False
    ).annotate(
        latest_value=Subquery(latest_measurement_subquery)
    )

    qs = Sector.objects.filter(archived=False).select_related('crop').prefetch_related(
        Prefetch('sensors', queryset=active_sensors_with_latest_data)
    )

    sectors = list(qs)

    UNITS_MAPPING = {
        'TEMP': '°C', 'HUM': '%', 'PH': 'pH', 'NIT': 'мг/кг'
    }

    for sector in sectors:
        sector.is_critical = False
        crop = sector.crop

        for sensor in sector.sensors.all():
            sensor.is_critical = False
            sensor.unit = UNITS_MAPPING.get(sensor.type, '')
            val = sensor.latest_value

            if val is None or not crop:
                continue

            if sensor.type == 'TEMP':
                if val < crop.min_temperature or val > crop.max_temperature:
                    sensor.is_critical = True
            elif sensor.type == 'HUM':
                if val < crop.min_humidity or val > crop.max_humidity:
                    sensor.is_critical = True
            elif sensor.type == 'PH':
                if val < crop.min_ph or val > crop.max_ph:
                    sensor.is_critical = True
            elif sensor.type == 'NIT':
                if val < crop.min_nitrogen or val > crop.max_nitrogen:
                    sensor.is_critical = True

            if sensor.is_critical:
                sector.is_critical = True

    return sectors


def api_realtime_measurements(request):
    sectors = get_annotated_sectors()

    response_data = []

    for sector in sectors:
        sensors_info_list = [
            {
                "serial": sensor.serial_number,
                "type": sensor.get_type_display(),
                "latest_value": sensor.latest_value if sensor.latest_value is not None else '—',
                "unit": sensor.unit,
                "is_critical": sensor.is_critical,
                "is_active": sensor.is_active
            }
            for sensor in sector.sensors.all()
        ]

        response_data.append({
            'id': sector.id,
            'is_critical': sector.is_critical,
            'status_text': 'Критичний' if sector.is_critical else 'В нормі',
            'sensors_info': sensors_info_list
        })

    return JsonResponse({'sectors': response_data})

class SectorListView(ListView):
    template_name = 'index.html'
    context_object_name = 'sectors'

    def get_queryset(self):
        return get_annotated_sectors()


class SectorCreateView(CreateView):
    template_name = 'sector_create_update.html'
    model = Sector
    form_class = SectorCreateForm
    success_url = reverse_lazy("dashboard")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['sectors'] = Sector.objects.filter(archived=False)
        return context


class SectorUpdateView(UpdateView):
    template_name = 'sector_create_update.html'
    queryset = Sector.objects.filter(archived=False)
    form_class = SectorUpdateForm
    success_url = reverse_lazy("dashboard")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['sectors'] = Sector.objects.filter(archived=False).exclude(pk=self.object.pk)
        return context


class SectorDeleteView(DeleteView):
    model = Sector
    success_url = reverse_lazy("dashboard")

    def form_valid(self, form):
        success_url = self.get_success_url()
        sector = self.get_object()
        sector.archived = True
        sector.save()
        sector.sensors.update(is_active=False, sector=None, offset_y=0, offset_x=0)
        return HttpResponseRedirect(success_url)
