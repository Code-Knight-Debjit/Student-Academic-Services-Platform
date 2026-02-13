"""
Django admin configuration for Results app.
"""

from django.contrib import admin
from django.utils.html import format_html
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
    list_display = ['is_window_open', 'window_start_date', 'window_end_date', 'fee_per_subject', 'updated_at']
    list_filter = ['is_window_open']
    
    fieldsets = (
        ('Window Status', {
            'fields': ('is_window_open', 'window_start_date', 'window_end_date')
        }),
        ('Fee Configuration', {
            'fields': ('fee_per_subject', 'max_subjects_per_request')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ['created_at', 'updated_at']
    
    def has_add_permission(self, request):
        # Only allow one configuration
        return not RevaluationConfiguration.objects.exists()
    
    def has_delete_permission(self, request, obj=None):
        # Don't allow deletion
        return False


@admin.register(RevaluationRequest)
class RevaluationRequestAdmin(admin.ModelAdmin):
    list_display = ['id', 'student', 'course_info', 'status', 'amount_paid', 'receipt_link', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['student__usn', 'student__name', 'result__course__course_code']
    readonly_fields = ['razorpay_order_id', 'razorpay_payment_id', 'razorpay_signature', 'original_marks', 'receipt_link', 'created_at', 'updated_at']
    
    fieldsets = (
        ('Student & Course', {
            'fields': ('student', 'result', 'original_marks')
        }),
        ('Payment Details', {
            'fields': ('razorpay_order_id', 'razorpay_payment_id', 'razorpay_signature', 'amount_paid')
        }),
        ('Status', {
            'fields': ('status', 'receipt_link')
        }),
        ('Revaluation Results', {
            'fields': ('revalued_marks', 'marks_changed', 'admin_remarks', 'processed_by', 'processed_at')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def course_info(self, obj):
        return f"{obj.result.course.course_code} - {obj.result.course.course_title}"
    course_info.short_description = 'Course'
    
    def receipt_link(self, obj):
        if obj.receipt_url:
            return format_html(
                '<a href="{}" target="_blank" class="button">📄 Download Receipt</a>',
                obj.receipt_url
            )
        return "No receipt"
    receipt_link.short_description = 'Receipt'


@admin.register(MakeupExamConfiguration)
class MakeupExamConfigurationAdmin(admin.ModelAdmin):
    list_display = ['is_registration_open', 'registration_start_date', 'exam_date', 'fee_per_subject', 'exam_center']
    list_filter = ['is_registration_open']
    
    fieldsets = (
        ('Registration Window', {
            'fields': ('is_registration_open', 'registration_start_date', 'registration_end_date')
        }),
        ('Exam Details', {
            'fields': ('exam_date', 'exam_center')
        }),
        ('Fee Configuration', {
            'fields': ('fee_per_subject', 'max_subjects_per_student')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ['created_at', 'updated_at']
    
    def has_add_permission(self, request):
        return not MakeupExamConfiguration.objects.exists()
    
    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(MakeupExamRequest)
class MakeupExamRequestAdmin(admin.ModelAdmin):
    list_display = ['id', 'student', 'exam_cycle', 'subject_count', 'status', 'verification_status', 'amount_paid', 'receipt_link', 'created_at']
    list_filter = ['status', 'admin_verified', 'proctor_verified', 'created_at']
    search_fields = ['student__usn', 'student__name', 'exam_cycle']
    filter_horizontal = ['subjects']
    
    fieldsets = (
        ('Student Information', {
            'fields': ('student', 'semester', 'exam_cycle', 'subjects')
        }),
        ('Payment Details', {
            'fields': ('razorpay_order_id', 'razorpay_payment_id', 'razorpay_signature', 'amount_paid')
        }),
        ('Status', {
            'fields': ('status', 'receipt_link', 'hall_ticket_link')
        }),
        ('Admin Verification', {
            'fields': ('admin_verified', 'admin_verified_by', 'admin_verified_at', 'admin_remarks')
        }),
        ('Proctor Verification', {
            'fields': ('proctor_verified', 'proctor_verified_by', 'proctor_verified_at', 'proctor_remarks')
        }),
        ('Exam Details', {
            'fields': ('exam_center', 'exam_date', 'reporting_time')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ['razorpay_order_id', 'razorpay_payment_id', 'razorpay_signature', 'receipt_link', 'hall_ticket_link', 'created_at', 'updated_at']
    
    def subject_count(self, obj):
        return obj.get_subject_count()
    subject_count.short_description = 'Subjects'
    
    def verification_status(self, obj):
        admin_icon = '✅' if obj.admin_verified else '⏳'
        proctor_icon = '✅' if obj.proctor_verified else '⏳'
        return format_html(
            '<span title="Admin">{}</span> <span title="Proctor">{}</span>',
            admin_icon, proctor_icon
        )
    verification_status.short_description = 'Verification'
    
    def receipt_link(self, obj):
        if obj.receipt_url:
            return format_html(
                '<a href="{}" target="_blank" class="button">📄 Receipt</a>',
                obj.receipt_url
            )
        return "No receipt"
    receipt_link.short_description = 'Receipt'
    
    def hall_ticket_link(self, obj):
        if obj.hall_ticket_url:
            return format_html(
                '<a href="{}" target="_blank" class="button">🎫 Hall Ticket</a>',
                obj.hall_ticket_url
            )
        elif obj.can_generate_hall_ticket():
            return "Ready to generate"
        return "Not available"
    hall_ticket_link.short_description = 'Hall Ticket'


@admin.register(StudentNotification)
class StudentNotificationAdmin(admin.ModelAdmin):
    list_display = ['student', 'notification_type', 'title', 'is_read', 'created_at']
    list_filter = ['notification_type', 'is_read', 'created_at']
    search_fields = ['student__usn', 'student__name', 'title', 'message']
    readonly_fields = ['created_at']
    
    fieldsets = (
        ('Notification Details', {
            'fields': ('student', 'notification_type', 'title', 'message')
        }),
        ('Status', {
            'fields': ('is_read',)
        }),
        ('Related Objects', {
            'fields': ('revaluation_request', 'makeup_exam_request'),
            'classes': ('collapse',)
        }),
        ('Timestamp', {
            'fields': ('created_at',)
        }),
    )
    
    def has_add_permission(self, request):
        # Notifications should be created programmatically
        return False


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ['action_type', 'user', 'student', 'created_at']
    list_filter = ['action_type', 'created_at']
    search_fields = ['description', 'student__usn', 'user__username']
    readonly_fields = ['user', 'student', 'action_type', 'description', 'ip_address', 'user_agent', 'metadata', 'created_at']
    
    fieldsets = (
        ('Action Details', {
            'fields': ('action_type', 'description')
        }),
        ('Related Objects', {
            'fields': ('user', 'student')
        }),
        ('Technical Details', {
            'fields': ('ip_address', 'user_agent', 'metadata'),
            'classes': ('collapse',)
        }),
        ('Timestamp', {
            'fields': ('created_at',)
        }),
    )
    
    def has_add_permission(self, request):
        # Audit logs should be created programmatically
        return False
    
    def has_delete_permission(self, request, obj=None):
        # Don't allow deletion of audit logs
        return False