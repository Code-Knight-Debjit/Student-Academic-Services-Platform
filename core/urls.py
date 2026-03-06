"""
URL patterns for Core app (home page).
"""

from django.urls import path
from results.views import home, admin_dashboard, bulk_upload, edit_result, analytics

urlpatterns = [
    path('', home, name='home'),
    path('admin-panel/', admin_dashboard, name='admin_panel'),
    path('admin-panel/upload/', bulk_upload, name='bulk_upload'),
    path('admin-panel/edit/<str:result_id>/', edit_result, name='edit_result'),
    path('admin-panel/analytics/', analytics, name='analytics'),
]
