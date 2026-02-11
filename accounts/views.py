"""
Authentication views.
"""

from django.contrib.auth import login, logout
from django.contrib.auth.views import LoginView
from django.shortcuts import redirect
from django.urls import reverse_lazy
from results.forms import CustomAuthenticationForm


class CustomLoginView(LoginView):
    """Custom login view with Tailwind styling."""
    form_class = CustomAuthenticationForm
    template_name = 'accounts/login.html'
    redirect_authenticated_user = True
    
    def get_success_url(self):
        return reverse_lazy('admin_panel')


def logout_view(request):
    """Logout view with session cleanup."""
    logout(request)
    request.session.flush()
    return redirect('home')

