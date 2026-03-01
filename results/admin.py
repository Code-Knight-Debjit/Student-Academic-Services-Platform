# ============================================================================
# COMPLETE ADMIN PANEL IMPLEMENTATION
# Student Management, Revaluation Processing, and Receipt Management
# ============================================================================

"""
PART 1: Updated admin.py with enhanced features
LOCATION: results/admin.py
"""

from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.db.models import Q
from .models import (
    Student,
    StudentMetadata,
    Course,
    Paper_Seeing,
    Result,
    UploadHistory,
    RevaluationConfiguration,
    PaperSeeingConfiguration,
    PaperSeeingRequest,
    RevaluationRequest,
    MakeupExamConfiguration,
    MakeupExamRequest,
    StudentNotification,
    AuditLog
)


# ============================================================================
# ENHANCED STUDENT ADMIN WITH SEARCH
# ============================================================================

@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ['usn', 'name', 'department', 'view_results_link', 'receipts_link']
    search_fields = ['usn', 'name', 'department']
    list_filter = ['semester', 'department']
    ordering = ['usn']
    list_per_page = 50
    
    # Enable advanced search
    search_help_text = "Search by USN, Name, or Department"
    
    def view_results_link(self, obj):
        """Link to view student's results."""
        return format_html(
            '<a href="{}" class="button">View Results</a>',
            reverse('admin:results_result_changelist') + f'?student__id__exact={obj.pk}'
        )
    view_results_link.short_description = 'Results'
    
    def receipts_link(self, obj):
        """Link to view student's receipts."""
        try:
            url = reverse('admin:student_receipts', args=[obj.pk])
            return format_html(
                '<a href="{}" class="button">📄 Receipts</a>',
                url
            )
        except:
            return "N/A"
    receipts_link.short_description = 'Receipts'
    
    # Custom actions
    actions = ['export_students']
    
    def export_students(self, request, queryset):
        """Export selected students to CSV."""
        import csv
        from django.http import HttpResponse
        
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="students.csv"'
        
        writer = csv.writer(response)
        writer.writerow(['USN', 'Name', 'Department', 'Batch'])
        
        for student in queryset:
            writer.writerow([student.usn, student.name, student.department or '', student.batch or ''])
        
        return response
    export_students.short_description = "Export selected students to CSV"


# ============================================================================
# ENHANCED REVALUATION REQUEST ADMIN WITH EDIT MARKS ACTION
# ============================================================================

@admin.register(RevaluationRequest)
class RevaluationRequestAdmin(admin.ModelAdmin):
    list_display = [
        'id', 
        'student_info', 
        'course_info', 
        'original_marks',
        'revalued_marks',
        'status', 
        'amount_paid', 
        'edit_marks_link',
        'receipt_link', 
        'created_at'
    ]
    list_filter = ['status', 'marks_changed', 'created_at']
    search_fields = [
        'student__usn', 
        'student__name', 
        'result__course__course_code',
        'result__course__course_title'
    ]
    readonly_fields = [
        'razorpay_order_id', 
        'razorpay_payment_id', 
        'razorpay_signature', 
        'original_marks', 
        'receipt_link', 
        'created_at', 
        'updated_at'
    ]
    
    list_per_page = 50
    date_hierarchy = 'created_at'
    
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
            'fields': ('revalued_marks', 'marks_changed', 'admin_remarks', 'processed_by', 'processed_at'),
            'description': 'To edit marks, use the "Edit Marks" button in the list view'
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def student_info(self, obj):
        return format_html(
            '<strong>{}</strong><br/><small>{}</small>',
            obj.student.usn,
            obj.student.name
        )
    student_info.short_description = 'Student'
    
    def course_info(self, obj):
        return format_html(
            '<strong>{}</strong><br/><small>{}</small>',
            obj.result.course.course_code,
            obj.result.course.course_title[:30] + ('...' if len(obj.result.course.course_title) > 30 else '')
        )
    course_info.short_description = 'Course'
    
    def edit_marks_link(self, obj):
        """Link to edit marks page."""
        if obj.status in ['PAID', 'PROCESSING']:
            url = reverse('admin_edit_revaluation', args=[obj.result.id])
            return format_html(
                '<a href="{}" class="button" style="background-color: #417690; color: white;">✏️ Edit Marks</a>',
                url
            )
        elif obj.status == 'COMPLETED':
            return format_html(
                '<span style="color: green;">✓ Completed</span>'
            )
        return '-'
    edit_marks_link.short_description = 'Action'
    
    def receipt_link(self, obj):
        if obj.receipt_url:
            return format_html(
                '<a href="{}" target="_blank" class="button">📄 Download</a>',
                obj.receipt_url
            )
        return "No receipt"
    receipt_link.short_description = 'Receipt'
    
    # Custom actions
    actions = ['mark_as_processing', 'export_requests']
    
    def mark_as_processing(self, request, queryset):
        updated = queryset.filter(status='PAID').update(status='PROCESSING')
        self.message_user(request, f'{updated} request(s) marked as processing.')
    mark_as_processing.short_description = "Mark as Processing"
    
    def export_requests(self, request, queryset):
        import csv
        from django.http import HttpResponse
        
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="revaluation_requests.csv"'
        
        writer = csv.writer(response)
        writer.writerow(['ID', 'USN', 'Student', 'Course', 'Original Marks', 'Revalued Marks', 'Status', 'Amount'])
        
        for req in queryset:
            writer.writerow([
                req.id,
                req.student.usn,
                req.student.name,
                req.result.course.course_code,
                req.original_marks,
                req.revalued_marks or '',
                req.status,
                req.amount_paid
            ])
        
        return response
    export_requests.short_description = "Export to CSV"


@admin.register(PaperSeeingRequest)
class PaperSeeingRequestAdmin(admin.ModelAdmin):
    list_display = [
        'id', 
        'student_info', 
        'course_info', 
        'original_marks',
        'status', 
        'amount_paid', 
        'receipt_link', 
        'created_at'
    ]
    list_filter = ['status', 'created_at']
    search_fields = [
        'student__usn', 
        'student__name', 
        'result__course__course_code',
        'result__course__course_title'
    ]
    readonly_fields = [
        'razorpay_order_id', 
        'razorpay_payment_id', 
        'razorpay_signature', 
        'original_marks', 
        'receipt_link', 
        'created_at', 
        'updated_at'
    ]
    
    list_per_page = 50
    date_hierarchy = 'created_at'
    
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
        ('Paper Seeing Results', {
            'fields': ('admin_remarks', 'processed_by', 'processed_at'),
            'description': ''
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def student_info(self, obj):
        return format_html(
            '<strong>{}</strong><br/><small>{}</small>',
            obj.student.usn,
            obj.student.name
        )
    student_info.short_description = 'Student'
    
    def course_info(self, obj):
        return format_html(
            '<strong>{}</strong><br/><small>{}</small>',
            obj.result.course.course_code,
            obj.result.course.course_title[:30] + ('...' if len(obj.result.course.course_title) > 30 else '')
        )
    course_info.short_description = 'Course'
    
    # def edit_marks_link(self, obj):
    #     """Link to edit marks page."""
    #     if obj.status in ['PAID', 'PROCESSING']:
    #         url = reverse('admin_edit_revaluation', args=[obj.result.id])
    #         return format_html(
    #             '<a href="{}" class="button" style="background-color: #417690; color: white;">✏️ Edit Marks</a>',
    #             url
    #         )
    #     elif obj.status == 'COMPLETED':
    #         return format_html(
    #             '<span style="color: green;">✓ Completed</span>'
    #         )
    #     return '-'
    # edit_marks_link.short_description = 'Action'
    
    def receipt_link(self, obj):
        if obj.receipt_url:
            return format_html(
                '<a href="{}" target="_blank" class="button">📄 Download</a>',
                obj.receipt_url
            )
        return "No receipt"
    receipt_link.short_description = 'Receipt'
    
    # Custom actions
    actions = ['mark_as_processing', 'export_requests']
    
    def mark_as_processing(self, request, queryset):
        updated = queryset.filter(status='PAID').update(status='PROCESSING')
        self.message_user(request, f'{updated} request(s) marked as processing.')
    mark_as_processing.short_description = "Mark as Processing"
    
    def export_requests(self, request, queryset):
        import csv
        from django.http import HttpResponse
        
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="revaluation_requests.csv"'
        
        writer = csv.writer(response)
        writer.writerow(['ID', 'USN', 'Student', 'Course', 'Original Marks', 'Revalued Marks', 'Status', 'Amount'])
        
        for req in queryset:
            writer.writerow([
                req.id,
                req.student.usn,
                req.student.name,
                req.result.course.course_code,
                req.original_marks,
                req.status,
                req.amount_paid
            ])
        
        return response
    export_requests.short_description = "Export to CSV"


# ============================================================================
# ENHANCED MAKEUP EXAM REQUEST ADMIN
# ============================================================================

@admin.register(MakeupExamRequest)
class MakeupExamRequestAdmin(admin.ModelAdmin):
    list_display = [
        'id', 
        'student_info', 
        'exam_cycle', 
        'subject_count', 
        'status', 
        'verification_status', 
        'amount_paid', 
        'receipt_link',
        'hall_ticket_link',
        'created_at'
    ]
    list_filter = ['status', 'admin_verified', 'proctor_verified', 'created_at']
    search_fields = ['student__usn', 'student__name', 'exam_cycle']
    filter_horizontal = ['subjects']
    list_per_page = 50
    date_hierarchy = 'created_at'
    
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
    
    readonly_fields = [
        'razorpay_order_id', 
        'razorpay_payment_id', 
        'razorpay_signature', 
        'receipt_link', 
        'hall_ticket_link', 
        'created_at', 
        'updated_at'
    ]
    
    def student_info(self, obj):
        return format_html(
            '<strong>{}</strong><br/><small>{}</small>',
            obj.student.usn,
            obj.student.name
        )
    student_info.short_description = 'Student'
    
    def subject_count(self, obj):
        return obj.get_subject_count()
    subject_count.short_description = 'Subjects'
    
    def verification_status(self, obj):
        admin_icon = '✅ Admin' if obj.admin_verified else '⏳ Admin'
        proctor_icon = '✅ Proctor' if obj.proctor_verified else '⏳ Proctor'
        return format_html(
            '<div>{}<br/>{}</div>',
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


# ============================================================================
# OTHER MODEL ADMINS (Keep as before)
# ============================================================================

@admin.register(StudentMetadata)
class StudentMetadataAdmin(admin.ModelAdmin):
    list_display = ['student', 'dob', 'admission_route']
    search_fields = ['student__usn', 'student__name']
    list_filter = ['admission_route']


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ['course_code', 'course_title', 'credits']
    search_fields = ['course_code', 'course_title']
    list_filter = ['credits']


@admin.register(Result)
class ResultAdmin(admin.ModelAdmin):
    list_display = ['student', 'course', 'semester', 'final_cie_marks', 'edit_link']
    search_fields = ['student__usn', 'course__course_code']
    list_filter = ['semester']
    
    def edit_link(self, obj):
        url = reverse('admin_edit_result', args=[obj.pk])
        return format_html(
            '<a href="{}" class="button">✏️ Edit</a>',
            url
        )
    edit_link.short_description = 'Action'


@admin.register(UploadHistory)
class UploadHistoryAdmin(admin.ModelAdmin):
    list_display = ['file_name', 'upload_type', 'uploaded_by', 'success', 'upload_date']
    list_filter = ['upload_type', 'success', 'upload_date']
    search_fields = ['file_name']
    readonly_fields = ['upload_date']


@admin.register(RevaluationConfiguration)
class RevaluationConfigurationAdmin(admin.ModelAdmin):
    list_display = ['is_window_open', 'window_start_date', 'window_end_date', 'fee_per_subject', 'updated_at']
    list_filter = ['is_window_open']
    
    def has_add_permission(self, request):
        return not RevaluationConfiguration.objects.exists()
    
    def has_delete_permission(self, request, obj=None):
        return False
    

@admin.register(PaperSeeingConfiguration)
class PaperSeeingConfigurationAdmin(admin.ModelAdmin):
    list_display = ['is_window_open', 'window_start_date', 'window_end_date', 'fee_per_subject', 'updated_at']
    list_filter = ['is_window_open']
    
    def has_add_permission(self, request):
        return not PaperSeeingConfiguration.objects.exists()
    
    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(MakeupExamConfiguration)
class MakeupExamConfigurationAdmin(admin.ModelAdmin):
    list_display = ['is_registration_open', 'registration_start_date', 'exam_date', 'fee_per_subject', 'exam_center']
    list_filter = ['is_registration_open']
    
    def has_add_permission(self, request):
        return not MakeupExamConfiguration.objects.exists()
    
    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(StudentNotification)
class StudentNotificationAdmin(admin.ModelAdmin):
    list_display = ['student', 'notification_type', 'title', 'is_read', 'created_at']
    list_filter = ['notification_type', 'is_read', 'created_at']
    search_fields = ['student__usn', 'student__name', 'title', 'message']
    readonly_fields = ['created_at']
    
    def has_add_permission(self, request):
        return False


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ['action_type', 'user', 'student', 'created_at']
    list_filter = ['action_type', 'created_at']
    search_fields = ['description', 'student__usn', 'user__username']
    readonly_fields = ['user', 'student', 'action_type', 'description', 'ip_address', 'user_agent', 'metadata', 'created_at']
    
    def has_add_permission(self, request):
        return False
    
    def has_delete_permission(self, request, obj=None):
        return False