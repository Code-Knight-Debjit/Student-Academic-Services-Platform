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

    def __str__(self):
        return f"{self.upload_type} - {self.file_name} - {self.upload_date}"

