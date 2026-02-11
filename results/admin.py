"""
Django admin configuration for Results app.
"""

from django.contrib import admin
from .models import Student, StudentMetadata, Course, Result, UploadHistory


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

