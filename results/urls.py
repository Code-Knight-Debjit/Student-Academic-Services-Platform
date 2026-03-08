"""
URL patterns for Results app.
"""

from django.urls import path
from . import views

urlpatterns = [
    path('download/<str:usn>/<int:semester>/', views.download_pdf, name='download_pdf'),
    path("download-receipt/<str:type>/<int:pk>/", views.download_receipt, name="download_receipt"),
    
#     path('receipt/<str:receipt_type>/<int:request_id>/', 
#           views.download_receipt, 
#           name='download_receipt'),
    
    path('revaluation/create-order/', 
         views.create_revaluation_order, 
         name='create_revaluation_order'),
    
    path('revaluation/verify-payment/', 
         views.verify_revaluation_payment, 
         name='verify_revaluation_payment'),   

    path('paperseeing/create-order/', 
         views.create_paper_seeing_order, 
         name='create_paper_seeing_order'),
    
    path('paperseeing/verify-payment/', 
         views.verify_paperseeing_payment, 
         name='verify_paper_seeing_payment'),

     
    # ========================================================================
    # NEW URLS - Makeup Exam
    # ========================================================================
#     path('makeup-exam/<str:usn>/<int:semester>/', 
#          views.makeup_exam_page, 
#          name='makeup_exam_page'),
    
#     path('makeup-exam/create-order/', 
#          views.create_makeup_exam_order, 
#          name='create_makeup_exam_order'),
    
#     path('makeup-exam/verify-payment/', 
#          views.verify_makeup_exam_payment, 
#          name='verify_makeup_exam_payment'),
    
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

    path('admin/student-search/', 
         views.admin_search_requests, 
         name='admin_student_list'), 

    path('admin/student-list/', 
         views.admin_student_list_requests, 
         name='admin_student_list_requests'), 

    path('admin/paperseeing-requests/', 
         views.admin_paperseeing_requests, 
         name='admin_paperseeing_requests'),
    
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
    # Admin Features - Edit Marks
    path('admin-panel/edit-revaluation/<int:result_id>/', 
         views.admin_edit_revaluation, 
         name='admin_edit_revaluation'),
    
    path('admin-panel/edit-result/<int:result_id>/', 
         views.admin_edit_result, 
         name='admin_edit_result'),
    
    # Admin Features - Student Receipts
    path('admin/student-receipts/<int:student_id>/', 
         views.student_receipts, 
         name='student_receipts'),
    
    path('admin/download-receipts/<int:student_id>/', 
         views.download_student_receipts, 
         name='download_student_receipts'),
     # Student Management
     path('admin-panel/students/', views.student_search, name='student_search'),
     path('admin-panel/student/<int:student_id>/', views.student_profile, name='student_profile'),

     # Revaluation Management
     path('admin-panel/revaluations/', views.revaluation_management, name='revaluation_management'),

     # paperseeing Management
     path('admin-panel/paperseeings/', views.paperseeing_management, name='paperseeing_management'),

     # Makeup Exam Management
     path('admin-panel/makeup-exams/', views.makeup_exam_management, name='makeup_exam_management'),
     path('admin-panel/makeup-verify/<int:request_id>/', views.admin_verify_makeup_ajax, name='admin_verify_makeup_ajax'),
     path('admin-panel/proctor-verify/<int:request_id>/', views.proctor_verify_makeup_ajax, name='proctor_verify_makeup_ajax'),
]