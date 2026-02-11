"""
URL patterns for Results app.
"""

from django.urls import path
from . import views

urlpatterns = [
    path('download/<str:usn>/<int:semester>/', views.download_pdf, name='download_pdf'),
]