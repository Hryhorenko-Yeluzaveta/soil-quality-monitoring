from django.contrib.auth.mixins import UserPassesTestMixin
from django.core.exceptions import PermissionDenied

class AdminRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.is_admin()

    def handle_no_permission(self):
        if self.request.user.is_authenticated:
            raise PermissionDenied("У вас немає прав для перегляду цієї сторінки.")
        return super().handle_no_permission()