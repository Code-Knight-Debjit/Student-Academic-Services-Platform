"""
Django admin configuration for Results app.
"""

from django.contrib import admin
from .models import (Student, StudentMetadata, Course, Result, UploadHistory,
                        RevaluationConfiguration, RevaluationRequest,
                        MakeupExamConfiguration, MakeupExamRequest,
                        StudentNotification, AuditLog
                    )

@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ['usn', 'name', 'department', 'semester', 'created_at']
    search_fields = ['usn', 'name', 'department']
    list_filter = ['semester', 'department']
    ordering = ['usn']


@admin.register(StudentMetadata)
class StudentMetadataAdmin(admin.ModelAdmin):
    list_display = ['student', 'dob', 'admission_route', 'created_at']
    search_fields = ['student__usn', 'student__name']
    list_filter = ['admission_route']
    raw_id_fields = ['student']


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ['course_code', 'course_title', 'semester', 'credits', 'created_at']
    search_fields = ['course_code', 'course_title']
    list_filter = ['semester']
    ordering = ['semester', 'course_code']


@admin.register(Result)
class ResultAdmin(admin.ModelAdmin):
    list_display = ['student', 'course', 'final_cie_marks', 'semester', 'academic_year']
    search_fields = ['student__usn', 'student__name', 'course__course_code', 'course__course_title']
    list_filter = ['semester', 'academic_year']
    raw_id_fields = ['student', 'course']
    ordering = ['student', 'semester']


@admin.register(UploadHistory)
class UploadHistoryAdmin(admin.ModelAdmin):
    list_display = ['upload_type', 'file_name', 'uploaded_by', 'records_processed', 
                    'records_created', 'records_updated', 'success', 'upload_date']
    list_filter = ['upload_type', 'success', 'upload_date']
    search_fields = ['file_name', 'uploaded_by__username']
    readonly_fields = ['upload_date']
    ordering = ['-upload_date']


@admin.register(RevaluationConfiguration)
class RevaluationConfigurationAdmin(admin.ModelAdmin):
    list_display = ['is_window_open', 'window_start_date', 'window_end_date', 'fee_per_subject']
    
    def has_add_permission(self, request):
        # Only allow one configuration
        return not RevaluationConfiguration.objects.exists()

@admin.register(RevaluationRequest)
class RevaluationRequestAdmin(admin.ModelAdmin):
    list_display = ['student', 'result', 'status', 'amount_paid', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['student__usn', 'student__name', 'result__course__course_code']
    readonly_fields = ['razorpay_order_id', 'razorpay_payment_id', 'created_at']

@admin.register(MakeupExamConfiguration)
class MakeupExamConfigurationAdmin(admin.ModelAdmin):
    list_display = ['is_registration_open', 'registration_start_date', 'exam_date', 'fee_per_subject']
    
    def has_add_permission(self, request):
        return not MakeupExamConfiguration.objects.exists()

@admin.register(MakeupExamRequest)
class MakeupExamRequestAdmin(admin.ModelAdmin):
    list_display = ['student', 'exam_cycle', 'status', 'admin_verified', 'proctor_verified', 'created_at']
    list_filter = ['status', 'admin_verified', 'proctor_verified']
    search_fields = ['student__usn', 'student__name', 'exam_cycle']
    filter_horizontal = ['subjects']

@admin.register(StudentNotification)
class StudentNotificationAdmin(admin.ModelAdmin):
    list_display = ['student', 'notification_type', 'title', 'is_read', 'created_at']
    list_filter = ['notification_type', 'is_read']
    search_fields = ['student__usn', 'title']

@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ['action_type', 'user', 'student', 'created_at']
    list_filter = ['action_type', 'created_at']
    search_fields = ['description', 'student__usn']
    readonly_fields = ['created_at']

