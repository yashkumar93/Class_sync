"""
Decorators and mixins for role-based access control.
"""
from functools import wraps
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.contrib.auth.mixins import LoginRequiredMixin


def role_required(*roles):
    """
    Decorator that restricts a view to users with specific role(s).
    Raises PermissionDenied (→ 403) if the user's role is not in the allowed set.
    """
    def decorator(view_func):
        @wraps(view_func)
        @login_required
        def wrapper(request, *args, **kwargs):
            if request.user.role not in roles:
                raise PermissionDenied
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator


class RoleRequiredMixin(LoginRequiredMixin):
    """
    Class-based view mixin that enforces role-based access.
    Set `allowed_roles = ['admin', 'faculty']` on the view class.
    """
    allowed_roles = []

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        if self.allowed_roles and request.user.role not in self.allowed_roles:
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)
