from django.views.generic import ListView

from farm_monitoring.models import Crop

class CropListView(ListView):
    template_name = 'crops.html'
    model = Crop
    context_object_name = 'crops'