from django.views.generic import ListView

from farm_monitoring.models import Sensor


class SensorListView(ListView):
    queryset = Sensor.objects.filter(archived=False)
    template_name = 'sensor_list.html'
    context_object_name = 'sensors'
    paginate_by = 10
    def get_queryset(self):
        queryset = Sensor.objects.filter(archived=False)
        selected_type = self.request.GET.get('type', None)
        if selected_type:
            queryset = queryset.filter(type=selected_type)

        search_query = self.request.GET.get('q', None)
        if search_query:
            queryset = queryset.filter(serial_number__icontains=search_query)

        active_only = self.request.GET.get('active_only', None)
        if active_only == 'true':
            queryset = queryset.filter(is_active=True)

        return queryset

    def get_context_data(self, **kwargs):
        context = super(SensorListView, self).get_context_data(**kwargs)
        context['types'] = Sensor.Type.choices
        context['selected_type'] = self.request.GET.get('type', None)

        query_params = self.request.GET.copy()
        if 'page' in query_params:
            del query_params['page']
        context['query_string'] = query_params.urlencode()
        page = context.get('page_obj')
        if page:
            context['custom_page_range'] = page.paginator.get_elided_page_range(
                page.number, on_each_side=2, on_ends=1
            )

        return context