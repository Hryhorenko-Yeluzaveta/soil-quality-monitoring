from django.db.models import OuterRef, Subquery, Prefetch
from django.urls import reverse_lazy
from django.views.generic import CreateView, UpdateView, ListView

from farm_monitoring.forms import SectorCreateForm, SectorUpdateForm
from farm_monitoring.models import Sector, Measurement, Sensor


class SectorListView(ListView):
    template_name = 'index.html'
    context_object_name = 'sectors'

    def get_queryset(self):
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

        for sector in sectors:
            sector.is_critical = False
            if not sector.crop:
                continue
            crop = sector.crop
            for sensor in sector.sensors.all():
                val = sensor.latest_value
                if val is None:
                    continue
                if sensor.type == 'TEMP':
                    if val < crop.min_temperature or val > crop.max_temperature:
                        sector.is_critical = True
                        break

                elif sensor.type == 'HUM':
                    if val < crop.min_humidity or val > crop.max_humidity:
                        sector.is_critical = True
                        break

                elif sensor.type == 'PH':
                    if val < crop.min_ph or val > crop.max_ph:
                        sector.is_critical = True
                        break

                elif sensor.type == 'NIT':
                    if val < crop.min_nitrogen or val > crop.max_nitrogen:
                        sector.is_critical = True
                        break
        return sectors

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