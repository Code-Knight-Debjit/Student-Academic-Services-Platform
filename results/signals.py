"""
Django signals for notifications and audit logging.

LOCATION: results/signals.py
"""

from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.utils import timezone
import logging

from .models import (
    RevaluationRequest,
    MakeupExamRequest,
    StudentNotification,
    AuditLog
)

from .cache import (
    invalidate_student_result,
    invalidate_all_results_for_student,
    invalidate_analytics,
)

logger = logging.getLogger(__name__)

# ============================================================================
# NOTIFICATION HELPER
# ============================================================================

def create_notification(student, notification_type, title, message, 
                       revaluation_request=None, makeup_exam_request=None):
    """
    Create a notification for a student.
    
    Args:
        student: Student instance
        notification_type: Type of notification
        title: Notification title
        message: Notification message
        revaluation_request: Optional RevaluationRequest instance
        makeup_exam_request: Optional MakeupExamRequest instance
    """
    StudentNotification.objects.create(
        student=student,
        notification_type=notification_type,
        title=title,
        message=message,
        revaluation_request=revaluation_request,
        makeup_exam_request=makeup_exam_request
    )


# ============================================================================
# AUDIT LOG HELPER
# ============================================================================

def log_audit(action_type, description, user=None, student=None, 
              ip_address=None, user_agent=None, metadata=None):
    """
    Create an audit log entry.
    
    Args:
        action_type: Type of action
        description: Action description
        user: User who performed the action
        student: Related student
        ip_address: IP address
        user_agent: User agent string
        metadata: Additional metadata dict
    """
    AuditLog.objects.create(
        user=user,
        student=student,
        action_type=action_type,
        description=description,
        ip_address=ip_address,
        user_agent=user_agent,
        metadata=metadata or {}
    )


# ============================================================================
# REVALUATION SIGNALS
# ============================================================================

@receiver(post_save, sender=RevaluationRequest)
def revaluation_request_created(sender, instance, created, **kwargs):
    """Signal when revaluation request is created."""
    if created:
        # Log creation
        log_audit(
            action_type='REVALUATION_CREATED',
            student=instance.student,
            description=f'Revaluation request created for {instance.result.course.course_code}',
            metadata={
                'course_code': instance.result.course.course_code,
                'original_marks': float(instance.original_marks),
                'amount': float(instance.amount_paid)
            }
        )


@receiver(post_save, sender=RevaluationRequest)
def revaluation_status_changed(sender, instance, created, **kwargs):
    """Signal when revaluation status changes."""
    if not created and instance.status == 'COMPLETED':
        # Notify student of completion
        marks_change = "increased" if instance.marks_changed else "unchanged"
        message = f'Revaluation for {instance.result.course.course_title} is completed. '
        
        if instance.marks_changed:
            message += f'Your marks have been updated from {instance.original_marks} to {instance.revalued_marks}.'
        else:
            message += f'Your marks remain {instance.original_marks}.'
        
        create_notification(
            student=instance.student,
            notification_type='REVALUATION_COMPLETED',
            title='Revaluation Results Available',
            message=message,
            revaluation_request=instance
        )
        
        # Log completion
        log_audit(
            action_type='REVALUATION_PROCESSED',
            student=instance.student,
            user=instance.processed_by,
            description=f'Revaluation processed for {instance.result.course.course_code}',
            metadata={
                'course_code': instance.result.course.course_code,
                'original_marks': float(instance.original_marks),
                'revalued_marks': float(instance.revalued_marks) if instance.revalued_marks else None,
                'marks_changed': instance.marks_changed
            }
        )


# ============================================================================
# MAKEUP EXAM SIGNALS
# ============================================================================

@receiver(post_save, sender=MakeupExamRequest)
def makeup_exam_request_created(sender, instance, created, **kwargs):
    """Signal when makeup exam request is created."""
    if created:
        # Log creation
        log_audit(
            action_type='MAKEUP_CREATED',
            student=instance.student,
            description=f'Makeup exam request created for {instance.get_subject_count()} subjects',
            metadata={
                'exam_cycle': instance.exam_cycle,
                'semester': instance.semester,
                'subject_count': instance.get_subject_count(),
                'amount': float(instance.amount_paid)
            }
        )


@receiver(post_save, sender=MakeupExamRequest)
def makeup_exam_admin_verified(sender, instance, created, **kwargs):
    """Signal when admin verifies makeup exam request."""
    if not created and instance.admin_verified and instance.admin_verified_at:
        # Check if this is a new verification (not an update)
        original = sender.objects.filter(pk=instance.pk).first()
        if original and not original.admin_verified:
            # Log verification
            log_audit(
                action_type='ADMIN_VERIFIED',
                student=instance.student,
                user=instance.admin_verified_by,
                description=f'Admin verified makeup exam request for {instance.exam_cycle}',
                metadata={
                    'exam_cycle': instance.exam_cycle,
                    'remarks': instance.admin_remarks
                }
            )


@receiver(post_save, sender=MakeupExamRequest)
def makeup_exam_proctor_verified(sender, instance, created, **kwargs):
    """Signal when proctor verifies makeup exam request."""
    if not created and instance.proctor_verified and instance.proctor_verified_at:
        # Check if this is a new verification
        original = sender.objects.filter(pk=instance.pk).first()
        if original and not original.proctor_verified:
            # Log verification
            log_audit(
                action_type='PROCTOR_VERIFIED',
                student=instance.student,
                user=instance.proctor_verified_by,
                description=f'Proctor verified makeup exam request for {instance.exam_cycle}',
                metadata={
                    'exam_cycle': instance.exam_cycle,
                    'remarks': instance.proctor_remarks
                }
            )
            
            # If both verified, update status to APPROVED
            if instance.admin_verified:
                instance.status = 'APPROVED'
                instance.save(update_fields=['status'])


# ============================================================================
# EMAIL NOTIFICATIONS (Optional Enhancement)
# ============================================================================

def send_email_notification(student, subject, message):
    """
    Send email notification to student.
    
    This is a placeholder - implement with your email backend.
    """
    from django.core.mail import send_mail
    from django.conf import settings
    
    try:
        if hasattr(student.metadata, 'email') and student.metadata.email:
            send_mail(
                subject=subject,
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[student.metadata.email],
                fail_silently=True
            )
    except Exception as e:
        # Log error but don't fail
        print(f"Email notification failed: {e}")


# ============================================================================
# WEBHOOK HANDLER (For Razorpay)
# ============================================================================

from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
import json


@csrf_exempt
def razorpay_webhook(request):
    """
    Handle Razorpay webhook callbacks.
    
    Add this to your URLs:
    path('webhooks/razorpay/', razorpay_webhook, name='razorpay_webhook'),
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    
    try:
        # Verify signature
        signature = request.headers.get('X-Razorpay-Signature')
        payload = request.body
        
        from .services.payment_service import RazorpayService
        razorpay = RazorpayService()
        
        if not razorpay.verify_webhook_signature(payload, signature):
            return JsonResponse({'error': 'Invalid signature'}, status=400)
        
        # Parse event
        event = json.loads(payload)
        event_type = event.get('event')
        
        if event_type == 'payment.captured':
            # Payment successful
            payment_entity = event.get('payload', {}).get('payment', {}).get('entity', {})
            order_id = payment_entity.get('order_id')
            
            # Update request status if needed
            # This is a backup in case frontend verification fails
            
        elif event_type == 'payment.failed':
            # Payment failed
            payment_entity = event.get('payload', {}).get('payment', {}).get('entity', {})
            order_id = payment_entity.get('order_id')
            
            # Mark request as failed or send notification
        
        return JsonResponse({'status': 'success'})
    
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
    



# ---------------------------------------------------------------------------
# Result model signals
# ---------------------------------------------------------------------------

def _on_result_change(instance, **kwargs):
    """
    Called whenever a Result row is created, updated, or deleted.

    Invalidates:
      1. The specific (usn, semester) result card so it is reloaded fresh.
      2. All analytics keys because aggregates (averages, top performers, …)
         depend on result data.
    """
    usn      = instance.student_id          # the USN is the PK of Student
    semester = instance.semester

    invalidate_student_result(usn, semester)
    invalidate_analytics()
    logger.info("Cache invalidated for Result change: USN=%s, Sem=%s", usn, semester)


# Register the same handler for both save and delete events.
# We import the model lazily via the `sender` string to avoid circular imports.
# Django resolves the dotted path 'results.Result' after all apps are loaded.

@receiver(post_save,   sender="results.Result")
@receiver(post_delete, sender="results.Result")
def on_result_change(sender, instance, **kwargs):
    _on_result_change(instance, **kwargs)


# ---------------------------------------------------------------------------
# Student / StudentMetadata model signals
# ---------------------------------------------------------------------------

@receiver(post_save,   sender="results.Student")
@receiver(post_delete, sender="results.Student")
def on_student_change(sender, instance, **kwargs):
    """
    If the Student record itself changes (name, department, etc.) we need to
    invalidate every semester result card for that student because the name
    is embedded in the cached result dict.
    """
    invalidate_all_results_for_student(instance.usn)
    logger.info("Cache invalidated for Student change: USN=%s", instance.usn)


@receiver(post_save,   sender="results.StudentMetadata")
@receiver(post_delete, sender="results.StudentMetadata")
def on_student_metadata_change(sender, instance, **kwargs):
    """
    StudentMetadata holds date-of-birth and admission route.
    A DOB change means the student might not pass the lookup auth check,
    so we purge their cached cards to avoid stale successful lookups.
    """
    usn = instance.student_id
    invalidate_all_results_for_student(usn)
    logger.info("Cache invalidated for StudentMetadata change: USN=%s", usn)


# ---------------------------------------------------------------------------
# UploadHistory model signals
# ---------------------------------------------------------------------------

@receiver(post_save, sender="results.UploadHistory")
def on_upload_history_change(sender, instance, **kwargs):
    """
    Whenever a new bulk upload completes, the upload history list cache
    and all analytics are stale.
    """
    from .cache import cache_delete, _upload_history_key  # local import avoids circular dep
    cache_delete(_upload_history_key())
    invalidate_analytics()
    logger.info("Cache invalidated after new UploadHistory record (id=%s).", instance.pk)

@receiver(post_save,   sender="results.RevaluationRequest")
@receiver(post_delete, sender="results.RevaluationRequest")
def on_reval_request_change(sender, instance, **kwargs):
    try:
        from .models import RevaluationRequest
        obj = RevaluationRequest.objects.select_related('result').get(pk=instance.pk)
        invalidate_student_result(instance.student_id, obj.result.semester)
    except Exception:
        pass  # Don't crash if result is deleted

@receiver(post_save,   sender="results.PaperSeeingRequest")
@receiver(post_delete, sender="results.PaperSeeingRequest")
def on_paperseeing_request_change(sender, instance, **kwargs):
    try:
        from .models import PaperSeeingRequest
        obj = PaperSeeingRequest.objects.select_related('result').get(pk=instance.pk)
        invalidate_student_result(instance.student_id, obj.result.semester)
    except Exception:
        pass  # Don't crash if result is deleted