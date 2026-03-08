from django.db import models

# Create your models here.
"""
Database models for Student Results System.
"""

from django.db import models
from django.core.validators import RegexValidator
from django.core.exceptions import ValidationError


class Student(models.Model):
    """Student master table."""
    usn = models.CharField(
        max_length=10,
        primary_key=True,
        validators=[
            RegexValidator(
                regex=r'^[A-Za-z0-9]{10}$',
                message='USN must be exactly 10 alphanumeric characters'
            )
        ]
    )
    name = models.CharField(max_length=200)
    department = models.CharField(max_length=100, blank=True, null=True)
    semester = models.IntegerField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'students'
        ordering = ['usn']
        indexes = [
            models.Index(fields=['usn'])
        ]

    def __str__(self):
        return f"{self.usn} - {self.name}"


class StudentMetadata(models.Model):
    """Student metadata including DOB and admission route."""
    ADMISSION_ROUTES = [
        ('COMEDK-KA', 'COMEDK-KA'),
        ('COMEDK-NON_KA', 'COMEDK-NON_KA'),
        ('KCET', 'KCET'),
        ('MANAGEMENT', 'Management'),
    ]

    student = models.OneToOneField(
        Student,
        on_delete=models.CASCADE,
        primary_key=True,
        related_name='metadata'
    )
    dob = models.DateField()
    admission_route = models.CharField(
        max_length=20,
        choices=ADMISSION_ROUTES,
        blank=True,
        null=True
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'student_metadata'
        indexes = [
            models.Index(fields=['student']),
        ]

    def __str__(self):
        return f"{self.student.usn} - DOB: {self.dob}"


class Course(models.Model):
    """Course/Subject master table."""
    course_code = models.CharField(max_length=20, unique=True)
    course_title = models.CharField(max_length=200)
    semester = models.IntegerField()
    credits = models.IntegerField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'courses'
        ordering = ['semester', 'course_code']
        indexes = [
            models.Index(fields=['course_code']),
        ]

    def __str__(self):
        return f"{self.course_code} - {self.course_title}"


class Result(models.Model):
    """Student result records."""
    student = models.ForeignKey(
        Student,
        on_delete=models.CASCADE,
        related_name='results'
    )
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name='results'
    )
    final_cie_marks = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        blank=True,
        null=True
    )
    marks_in_words = models.CharField(max_length=100, blank=True, null=True)
    academic_year = models.CharField(max_length=20, blank=True, null=True)
    scheme = models.CharField(max_length=50, blank=True, null=True)
    semester = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'results'
        unique_together = ['student', 'course']
        ordering = ['student', 'semester', 'course']
        indexes = [
            models.Index(fields=['student', 'semester']),
        ]

    def __str__(self):
        return f"{self.student.usn} - {self.course.course_code} - {self.final_cie_marks}"


class Paper_Seeing(models.Model):
    """Student Paper Seeing records."""
    student = models.ForeignKey(
        Student,
        on_delete=models.CASCADE,
        related_name='paper_seeings'
    )
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name='paper_seeings'
    )
    final_cie_marks = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        blank=True,
        null=True
    )
    marks_in_words = models.CharField(max_length=100, blank=True, null=True)
    academic_year = models.CharField(max_length=20, blank=True, null=True)
    scheme = models.CharField(max_length=50, blank=True, null=True)
    semester = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'paper_seeings'
        unique_together = ['student', 'course']
        ordering = ['student', 'semester', 'course']
        indexes = [
            models.Index(fields=['student', 'semester']),
        ]

    def __str__(self):
        return f"{self.student.usn} - {self.course.course_code} - {self.final_cie_marks}"


class UploadHistory(models.Model):
    """Track Excel/CSV upload history."""
    UPLOAD_TYPES = [
        ('RESULTS', 'Results Data'),
        ('METADATA', 'Student Metadata'),
    ]

    upload_type = models.CharField(max_length=20, choices=UPLOAD_TYPES)
    file_name = models.CharField(max_length=255)
    uploaded_by = models.ForeignKey(
        'auth.User',
        on_delete=models.SET_NULL,
        null=True
    )
    records_processed = models.IntegerField(default=0)
    records_created = models.IntegerField(default=0)
    records_updated = models.IntegerField(default=0)
    records_skipped = models.IntegerField(default=0)
    upload_date = models.DateTimeField(auto_now_add=True)
    success = models.BooleanField(default=True)
    error_message = models.TextField(blank=True, null=True)

    class Meta:
        db_table = 'upload_history'
        ordering = ['-upload_date']
        indexes = [
            models.Index(fields=['upload_type', 'upload_date']),
        ]

    def __str__(self):
        return f"{self.upload_type} - {self.file_name} - {self.upload_date}"

"""
Extended models for Revaluation and Makeup Examination features.

LOCATION: results/models_extended.py

Add these models to your existing results/models.py or import from this file.
"""

from django.db import models
from django.core.validators import MinValueValidator
from django.utils import timezone
from .models import Student, Course, Result


class RevaluationConfiguration(models.Model):
    """Global revaluation settings managed by admin.""" 
    
    is_window_open = models.BooleanField(default=False)
    window_start_date = models.DateTimeField(null=True, blank=True)
    window_end_date = models.DateTimeField(null=True, blank=True)
    fee_per_subject = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=500.00,
        validators=[MinValueValidator(0)]
    )
    max_subjects_per_request = models.IntegerField(default=5)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'revaluation_configuration'
        verbose_name = 'Revaluation Configuration'
        verbose_name_plural = 'Revaluation Configuration'
        indexes = [
            models.Index(fields=['is_window_open']),
        ]
    
    def __str__(self):
        status = "Open" if self.is_window_open else "Closed"
        return f"Revaluation Window - {status}"
    
    def is_active(self):
        """Check if revaluation window is currently active."""
        if not self.is_window_open:
            return False
        
        now = timezone.now()
        if self.window_start_date and now < self.window_start_date:
            return False
        if self.window_end_date and now > self.window_end_date:
            return False
        
        return True


class RevaluationRequest(models.Model):
    """Student revaluation request with payment tracking."""
    
    STATUS_CHOICES = [
        ('PENDING', 'Pending Payment'),
        ('PAID', 'Payment Completed'),
        ('PROCESSING', 'Under Review'),
        ('COMPLETED', 'Revaluation Completed'),
        ('REJECTED', 'Rejected'),
        ('CANCELLED', 'Cancelled'),
    ]
    
    student = models.ForeignKey(
        Student,
        on_delete=models.CASCADE,
        related_name='revaluation_requests'
    )
    result = models.ForeignKey(
        Result,
        on_delete=models.CASCADE,
        related_name='revaluation_requests'
    )
    
    # Payment details
    razorpay_order_id = models.CharField(max_length=100, unique=True)
    razorpay_payment_id = models.CharField(max_length=100, blank=True, null=True)
    razorpay_signature = models.CharField(max_length=255, blank=True, null=True)
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2)
    
    # Status and tracking
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    receipt_url = models.CharField(max_length=500, blank=True, null=True)
    
    # Revaluation results
    original_marks = models.DecimalField(max_digits=5, decimal_places=2)
    revalued_marks = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        blank=True,
        null=True
    )
    marks_changed = models.BooleanField(default=False)
    
    # Admin fields
    admin_remarks = models.TextField(blank=True, null=True)
    processed_by = models.ForeignKey(
        'auth.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='processed_revaluations'
    )
    processed_at = models.DateTimeField(null=True, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'revaluation_requests'
        unique_together = ['student', 'result']
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['student', 'status']),
            models.Index(fields=['razorpay_order_id']),
        ]
    
    def __str__(self):
        return f"{self.student.usn} - {self.result.course.course_code} - {self.status}"
    
    def save(self, *args, **kwargs):
        # Store original marks on creation
        if not self.pk and not self.original_marks:
            self.original_marks = self.result.final_cie_marks
        super().save(*args, **kwargs)


class PaperSeeingConfiguration(models.Model):
    """Global Paper Seeing settings managed by admin.""" 
    
    is_window_open = models.BooleanField(default=False)
    window_start_date = models.DateTimeField(null=True, blank=True)
    window_end_date = models.DateTimeField(null=True, blank=True)
    fee_per_subject = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=1000.00,
        validators=[MinValueValidator(0)]
    )
    max_subjects_per_request = models.IntegerField(default=5)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'paper_seeing_configuration'
        verbose_name = 'Paper Seeing Configuration'
        verbose_name_plural = 'Paper Seeing Configuration'
        indexes = [
            models.Index(fields=['is_window_open']),
        ]
    
    def __str__(self):
        status = "Open" if self.is_window_open else "Closed"
        return f"Paper Seeing Window - {status}"
    
    def is_active(self):
        """Check if paper seeing window is currently active."""
        if not self.is_window_open:
            return False
        
        now = timezone.now()
        if self.window_start_date and now < self.window_start_date:
            return False
        if self.window_end_date and now > self.window_end_date:
            return False
        
        return True


class PaperSeeingRequest(models.Model):
    """Student Paper Seeing request with payment tracking."""
    
    STATUS_CHOICES = [
        ('PENDING', 'Pending Payment'),
        ('PAID', 'Payment Completed'),
        ('PROCESSING', 'Under Review'),
        ('COMPLETED', 'Revaluation Completed'),
        ('REJECTED', 'Rejected'),
        ('CANCELLED', 'Cancelled'),
    ]
    
    student = models.ForeignKey(
        Student,
        on_delete=models.CASCADE,
        related_name='paper_seeing_requests'
    )
    result = models.ForeignKey(
        Result,
        on_delete=models.CASCADE,
        related_name='paper_seeing_requests'
    )
    
    # Payment details
    razorpay_order_id = models.CharField(max_length=100, unique=True)
    razorpay_payment_id = models.CharField(max_length=100, blank=True, null=True)
    razorpay_signature = models.CharField(max_length=255, blank=True, null=True)
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2)
    
    # Status and tracking
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    receipt_url = models.CharField(max_length=500, blank=True, null=True)
    
    # Paper Seeing results
    original_marks = models.DecimalField(max_digits=5, decimal_places=2)
    # revalued_marks = models.DecimalField(
    #     max_digits=5,
    #     decimal_places=2,
    #     blank=True,
    #     null=True
    # )
    # marks_changed = models.BooleanField(default=False)
    
    # Admin fields
    admin_remarks = models.TextField(blank=True, null=True)
    processed_by = models.ForeignKey(
        'auth.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='processed_paper_seeing_requests'
    )
    processed_at = models.DateTimeField(null=True, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'paper_seeing_requests'
        unique_together = ['student', 'result']
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['student', 'status']),
            models.Index(fields=['razorpay_order_id']),
        ]
    
    def __str__(self):
        return f"{self.student.usn} - {self.result.course.course_code} - {self.status}"
    
    def save(self, *args, **kwargs):
        # Store original marks on creation
        if not self.pk and not self.original_marks:
            self.original_marks = self.result.final_cie_marks
        super().save(*args, **kwargs)


class MakeupExamConfiguration(models.Model):
    """Global makeup exam settings."""
    
    is_registration_open = models.BooleanField(default=False)
    registration_start_date = models.DateTimeField(null=True, blank=True)
    registration_end_date = models.DateTimeField(null=True, blank=True)
    exam_date = models.DateField(null=True, blank=True)
    exam_center = models.CharField(max_length=200, blank=True)
    fee_per_subject = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=1000.00,
        validators=[MinValueValidator(0)]
    )
    max_subjects_per_student = models.IntegerField(default=5)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'makeup_exam_configuration'
        verbose_name = 'Makeup Exam Configuration'
        verbose_name_plural = 'Makeup Exam Configuration'
        indexes = [
            models.Index(fields=['is_registration_open']),
        ]
    
    def __str__(self):
        status = "Open" if self.is_registration_open else "Closed"
        return f"Makeup Exam Registration - {status}"
    
    def is_active(self):
        """Check if registration window is currently active."""
        if not self.is_registration_open:
            return False
        
        now = timezone.now()
        if self.registration_start_date and now < self.registration_start_date:
            return False
        if self.registration_end_date and now > self.registration_end_date:
            return False
        
        return True


class MakeupExamRequest(models.Model):
    """Student makeup exam registration with payment."""
    
    STATUS_CHOICES = [
        ('PENDING', 'Pending Payment'),
        ('PAID', 'Payment Completed'),
        ('ADMIN_VERIFIED', 'Admin Verified'),
        ('PROCTOR_VERIFIED', 'Proctor Verified'),
        ('APPROVED', 'Approved - Hall Ticket Ready'),
        ('REJECTED', 'Rejected'),
        ('CANCELLED', 'Cancelled'),
        ('COMPLETED', 'Exam Completed'),
    ]
    
    student = models.ForeignKey(
        Student,
        on_delete=models.CASCADE,
        related_name='makeup_exam_requests'
    )
    subjects = models.ManyToManyField(
        Course,
        related_name='makeup_exam_requests'
    )
    semester = models.IntegerField()
    exam_cycle = models.CharField(max_length=50)  # e.g., "2024-MAKEUP-1"
    
    # Payment details
    razorpay_order_id = models.CharField(max_length=100, unique=True)
    razorpay_payment_id = models.CharField(max_length=100, blank=True, null=True)
    razorpay_signature = models.CharField(max_length=255, blank=True, null=True)
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2)
    
    # Status and verification
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    receipt_url = models.CharField(max_length=500, blank=True, null=True)
    hall_ticket_url = models.CharField(max_length=500, blank=True, null=True)
    
    # Verification tracking
    admin_verified = models.BooleanField(default=False)
    admin_verified_by = models.ForeignKey(
        'auth.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='admin_verified_makeup_exams'
    )
    admin_verified_at = models.DateTimeField(null=True, blank=True)
    admin_remarks = models.TextField(blank=True, null=True)
    
    proctor_verified = models.BooleanField(default=False)
    proctor_verified_by = models.ForeignKey(
        'auth.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='proctor_verified_makeup_exams'
    )
    proctor_verified_at = models.DateTimeField(null=True, blank=True)
    proctor_remarks = models.TextField(blank=True, null=True)
    
    # Exam details
    exam_center = models.CharField(max_length=200, blank=True)
    exam_date = models.DateField(null=True, blank=True)
    reporting_time = models.TimeField(null=True, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'makeup_exam_requests'
        unique_together = ['student', 'exam_cycle']
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['student', 'status']),
            models.Index(fields=['razorpay_order_id']),
            models.Index(fields=['exam_cycle']),
        ]
    
    def __str__(self):
        return f"{self.student.usn} - {self.exam_cycle} - {self.status}"
    
    def can_generate_hall_ticket(self):
        """Check if hall ticket can be generated."""
        return (
            self.status == 'APPROVED' and
            self.admin_verified and
            self.proctor_verified and
            bool(self.razorpay_payment_id)
        )
    
    def get_subject_count(self):
        """Get number of subjects registered."""
        return self.subjects.count()
    
    def calculate_total_fee(self):
        """Calculate total fee based on subjects."""
        try:
            config = MakeupExamConfiguration.objects.first()
            if config:
                return self.get_subject_count() * config.fee_per_subject
        except:
            pass
        return 0


class StudentNotification(models.Model):
    """Student notification system."""
    
    NOTIFICATION_TYPES = [
        ('PAYMENT_SUCCESS', 'Payment Successful'),
        ('REQUEST_SUBMITTED', 'Request Submitted'),
        ('HALL_TICKET_READY', 'Hall Ticket Ready'),
        ('ADMIN_VERIFIED', 'Admin Verified'),
        ('PROCTOR_VERIFIED', 'Proctor Verified'),
        ('REQUEST_REJECTED', 'Request Rejected'),
        ('REVALUATION_COMPLETED', 'Revaluation Completed'),
    ]
    
    student = models.ForeignKey(
        Student,
        on_delete=models.CASCADE,
        related_name='notifications'
    )
    notification_type = models.CharField(max_length=30, choices=NOTIFICATION_TYPES)
    title = models.CharField(max_length=200)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    
    # Related objects (optional)
    revaluation_request = models.ForeignKey(
        RevaluationRequest,
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )
    makeup_exam_request = models.ForeignKey(
        MakeupExamRequest,
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'student_notifications'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['student', 'is_read']),
        ]
    
    def __str__(self):
        return f"{self.student.usn} - {self.notification_type}"


class AuditLog(models.Model):
    """Audit trail for critical operations."""
    
    ACTION_TYPES = [
        ('REVALUATION_CREATED', 'Revaluation Request Created'),
        ('REVALUATION_PAID', 'Revaluation Payment Completed'),
        ('REVALUATION_PROCESSED', 'Revaluation Processed'),
        ('MAKEUP_CREATED', 'Makeup Exam Request Created'),
        ('MAKEUP_PAID', 'Makeup Exam Payment Completed'),
        ('ADMIN_VERIFIED', 'Admin Verification'),
        ('PROCTOR_VERIFIED', 'Proctor Verification'),
        ('HALL_TICKET_GENERATED', 'Hall Ticket Generated'),
    ]
    
    user = models.ForeignKey(
        'auth.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    student = models.ForeignKey(
        Student,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    action_type = models.CharField(max_length=30, choices=ACTION_TYPES)
    description = models.TextField()
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True, null=True)
    
    # Metadata
    metadata = models.JSONField(default=dict, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'audit_logs'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['action_type', 'created_at']),
            models.Index(fields=['student', 'created_at']),
        ]
    
    def __str__(self):
        return f"{self.action_type} - {self.created_at}"
