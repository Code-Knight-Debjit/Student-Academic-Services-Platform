"""
URL patterns for Results app.
"""

from django.urls import path
from . import views

urlpatterns = [
    path('download/<str:usn>/<int:semester>/', views.download_pdf, name='download_pdf'),
    
    path('revaluation/create-order/', 
         views.create_revaluation_order, 
         name='create_revaluation_order'),
    
    path('revaluation/verify-payment/', 
         views.verify_revaluation_payment, 
         name='verify_revaluation_payment'),
    
    
    # ========================================================================
    # NEW URLS - Makeup Exam
    # ========================================================================
    path('makeup-exam/<str:usn>/<int:semester>/', 
         views.makeup_exam_page, 
         name='makeup_exam_page'),
    
    path('makeup-exam/create-order/', 
         views.create_makeup_exam_order, 
         name='create_makeup_exam_order'),
    
    path('makeup-exam/verify-payment/', 
         views.verify_makeup_exam_payment, 
         name='verify_makeup_exam_payment'),
    
    path('makeup-exam/hall-ticket/<int:request_id>/', 
         views.download_hall_ticket, 
         name='download_hall_ticket'),
    
    
    # ========================================================================
    # NEW URLS - Admin Management (OPTIONAL - if you create separate views)
    # ========================================================================
    # Uncomment these if you create separate admin view functions
    # Otherwise, use Django admin interface
    
    path('admin/revaluation-requests/', 
         views.admin_revaluation_requests, 
         name='admin_revaluation_requests'),
    
    path('admin/makeup-exam-requests/', 
         views.admin_makeup_exam_requests, 
         name='admin_makeup_exam_requests'),
    
    path('admin/makeup-exam/verify/<int:request_id>/', 
         views.admin_verify_makeup_request, 
         name='admin_verify_makeup_request'),
    
    
    # ========================================================================
    # NEW URLS - Proctor Verification (OPTIONAL)
    # ========================================================================
    # Uncomment these if you create separate proctor view functions
    
    path('proctor/makeup-exam-requests/', 
         views.proctor_makeup_exam_requests, 
         name='proctor_makeup_exam_requests'),
    
    path('proctor/makeup-exam/verify/<int:request_id>/', 
         views.proctor_verify_makeup_request, 
         name='proctor_verify_makeup_request'),
]