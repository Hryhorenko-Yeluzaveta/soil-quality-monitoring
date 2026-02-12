from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView

from farm_monitoring.forms import CropForm
from farm_monitoring.models import Crop

class CropListView(ListView):
    template_name = 'crops.html'
    model = Crop
    context_object_name = 'crops'

class CropCreateView(CreateView):
    template_name = 'crop_form.html'
    model = Crop
    form_class = CropForm
    success_url = reverse_lazy("crops")