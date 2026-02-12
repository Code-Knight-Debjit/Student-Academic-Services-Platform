"""
URL configuration for Student Results System.
"""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from results.signals import razorpay_webhook

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('core.urls')),
    path('results/', include('results.urls')),
    path('accounts/', include('accounts.urls')),
    path('webhooks/razorpay/', razorpay_webhook, name='razorpay_webhook'),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
