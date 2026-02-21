from django.http import HttpResponseRedirect
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DeleteView

from farm_monitoring.forms import CropCreateForm, CropUpdateForm
from farm_monitoring.models import Crop

class CropListView(ListView):
    template_name = 'crops.html'
    queryset = Crop.objects.filter(archived=False)
    context_object_name = 'crops'
    def get_queryset(self):
        queryset = Crop.objects.filter(archived=False)
        selected_category = self.request.GET.get('category', None)
        if selected_category:
            queryset = queryset.filter(category=selected_category)
        return queryset
    def get_context_data(self, **kwargs):
        context = super(CropListView, self).get_context_data(**kwargs)
        context['categories'] = Crop.Category.choices
        context['selected_category'] = self.request.GET.get('category', None)
        return context

class CropCreateView(CreateView):
    template_name = 'crop_form.html'
    model = Crop
    form_class = CropCreateForm
    success_url = reverse_lazy("crops")

class CropUpdateView(UpdateView):
    template_name = 'crop_update_form.html'
    queryset = Crop.objects.filter(archived=False)
    form_class = CropUpdateForm
    success_url = reverse_lazy("crops")

class CropDeleteView(DeleteView):
    model = Crop
    success_url = reverse_lazy("crops")

    def form_valid(self, form):
        success_url = self.get_success_url()
        self.object.archived = True
        self.object.save()
        return HttpResponseRedirect(success_url)
