from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView

from farm_monitoring.forms import CropCreateForm, CropUpdateForm
from farm_monitoring.models import Crop

class CropListView(ListView):
    template_name = 'crops.html'
    model = Crop
    context_object_name = 'crops'

class CropCreateView(CreateView):
    template_name = 'crop_form.html'
    model = Crop
    form_class = CropCreateForm
    success_url = reverse_lazy("crops")

class CropUpdateView(UpdateView):
    template_name = 'crop_update_form.html'
    model = Crop
    form_class = CropUpdateForm
    success_url = reverse_lazy("crops")