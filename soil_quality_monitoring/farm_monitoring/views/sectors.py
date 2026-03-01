from django.urls import reverse_lazy
from django.views.generic import CreateView, UpdateView

from farm_monitoring.forms import SectorCreateForm, SectorUpdateForm
from farm_monitoring.models import Sector


class SectorCreateView(CreateView):
    template_name = 'sector_create_update.html'
    model = Sector
    form_class = SectorCreateForm
    success_url = reverse_lazy("dashboard")

class SectorUpdateView(UpdateView):
    template_name = 'sector_create_update.html'
    queryset = Sector.objects.filter(archived=False)
    form_class = SectorUpdateForm
    success_url = reverse_lazy("dashboard")