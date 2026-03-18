from django.contrib import messages
from django.contrib.auth.mixins import UserPassesTestMixin, LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.db.models import Q
from django.http import HttpResponseRedirect
from django.urls import reverse_lazy
from django.views.generic import ListView, DeleteView, CreateView, UpdateView

from farm_monitoring.forms import UserForm
from farm_monitoring.models import User


class AdminRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.is_admin()

    def handle_no_permission(self):
        if self.request.user.is_authenticated:
            raise PermissionDenied("У вас немає прав для перегляду цієї сторінки.")
        return super().handle_no_permission()

class UserListView(AdminRequiredMixin, ListView):
    model = User
    template_name = 'user_list.html'
    context_object_name = 'users'
    paginate_by = 10

    def get_queryset(self):
        queryset = User.objects.all().order_by('-date_joined')

        selected_role = self.request.GET.get('role', None)
        if selected_role:
            queryset = queryset.filter(role=selected_role)

        search_query = self.request.GET.get('q', None)
        if search_query:
            queryset = queryset.filter(
                Q(username__icontains=search_query) |
                Q(first_name__icontains=search_query) |
                Q(last_name__icontains=search_query) |
                Q(email__icontains=search_query)
            )

        active_only = self.request.GET.get('active_only', None)
        if active_only == 'true':
            queryset = queryset.filter(is_active=True)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context['roles'] = User.ROLE_CHOICES
        context['selected_role'] = self.request.GET.get('role', None)

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


class UserDeleteView(AdminRequiredMixin, DeleteView):
    model = User
    success_url = reverse_lazy("users")

    def form_valid(self, form):
        success_url = self.get_success_url()
        user_to_delete = self.get_object()

        if user_to_delete == self.request.user:
            messages.error(self.request, "Ви не можете видалити власний обліковий запис.")
            return HttpResponseRedirect(success_url)

        user_to_delete.is_active = False
        user_to_delete.save()
        return HttpResponseRedirect(success_url)

class UserCreateView(AdminRequiredMixin, CreateView):
    model = User
    form_class = UserForm
    template_name = 'user_create_update_form.html'
    success_url = reverse_lazy("users")

class UserUpdateView(AdminRequiredMixin, UpdateView):
    model = User
    form_class = UserForm
    template_name = 'user_create_update_form.html'
    success_url = reverse_lazy("users")