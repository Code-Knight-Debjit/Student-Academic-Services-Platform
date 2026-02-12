"""
Razorpay Payment Service for Revaluation and Makeup Exams.

LOCATION: results/services/payment_service.py
"""

import razorpay
import hmac
import hashlib
from django.conf import settings
from django.utils import timezone
from decimal import Decimal


class RazorpayService:
    """Centralized Razorpay payment handling service."""
    
    def __init__(self):
        self.client = razorpay.Client(
            auth=(
                settings.RAZORPAY_KEY_ID,
                settings.RAZORPAY_KEY_SECRET
            )
        )
    
    def create_order(self, amount, receipt_id, notes=None):
        """
        Create a Razorpay order.
        
        Args:
            amount: Amount in INR (will be converted to paise)
            receipt_id: Unique receipt identifier
            notes: Additional metadata
        
        Returns:
            dict: Order details from Razorpay
        """
        amount_in_paise = int(Decimal(amount) * 100)
        
        order_data = {
            'amount': amount_in_paise,
            'currency': 'INR',
            'receipt': receipt_id,
            'payment_capture': 1  # Auto capture
        }
        
        if notes:
            order_data['notes'] = notes
        
        try:
            order = self.client.order.create(data=order_data)
            return {
                'success': True,
                'order_id': order['id'],
                'amount': order['amount'],
                'currency': order['currency'],
                'receipt': order['receipt']
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def verify_payment_signature(self, order_id, payment_id, signature):
        """
        Verify Razorpay payment signature.
        
        Args:
            order_id: Razorpay order ID
            payment_id: Razorpay payment ID
            signature: Signature from Razorpay
        
        Returns:
            bool: True if signature is valid
        """
        try:
            # Generate expected signature
            message = f"{order_id}|{payment_id}"
            generated_signature = hmac.new(
                settings.RAZORPAY_KEY_SECRET.encode(),
                message.encode(),
                hashlib.sha256
            ).hexdigest()
            
            return hmac.compare_digest(generated_signature, signature)
        
        except Exception:
            return False
    
    def verify_webhook_signature(self, payload, signature):
        """
        Verify webhook signature from Razorpay.
        
        Args:
            payload: Raw request body
            signature: X-Razorpay-Signature header
        
        Returns:
            bool: True if signature is valid
        """
        try:
            expected_signature = hmac.new(
                settings.RAZORPAY_WEBHOOK_SECRET.encode(),
                payload,
                hashlib.sha256
            ).hexdigest()
            
            return hmac.compare_digest(expected_signature, signature)
        
        except Exception:
            return False
    
    def fetch_payment(self, payment_id):
        """
        Fetch payment details from Razorpay.
        
        Args:
            payment_id: Razorpay payment ID
        
        Returns:
            dict: Payment details
        """
        try:
            payment = self.client.payment.fetch(payment_id)
            return {
                'success': True,
                'payment': payment
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def refund_payment(self, payment_id, amount=None, notes=None):
        """
        Process refund for a payment.
        
        Args:
            payment_id: Razorpay payment ID
            amount: Amount to refund (None for full refund)
            notes: Refund notes
        
        Returns:
            dict: Refund details
        """
        try:
            refund_data = {}
            
            if amount:
                refund_data['amount'] = int(Decimal(amount) * 100)
            
            if notes:
                refund_data['notes'] = notes
            
            refund = self.client.payment.refund(payment_id, refund_data)
            
            return {
                'success': True,
                'refund_id': refund['id'],
                'amount': refund['amount'],
                'status': refund['status']
            }
        
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }


class RevaluationPaymentService:
    """Service for handling revaluation payments."""
    
    def __init__(self):
        self.razorpay = RazorpayService()
    
    def create_revaluation_order(self, student, result, config):
        """
        Create payment order for revaluation.
        
        Args:
            student: Student instance
            result: Result instance
            config: RevaluationConfiguration instance
        
        Returns:
            dict: Order details or error
        """
        from results.models_extended import RevaluationRequest
        
        # Check if request already exists
        existing = RevaluationRequest.objects.filter(
            student=student,
            result=result,
            status__in=['PENDING', 'PAID', 'PROCESSING']
        ).first()
        
        if existing:
            return {
                'success': False,
                'error': 'Revaluation request already exists for this subject'
            }
        
        # Generate unique receipt ID
        receipt_id = f"REVAL-{student.usn}-{result.course.course_code}-{timezone.now().strftime('%Y%m%d%H%M%S')}"
        
        # Create Razorpay order
        order_response = self.razorpay.create_order(
            amount=config.fee_per_subject,
            receipt_id=receipt_id,
            notes={
                'student_usn': student.usn,
                'student_name': student.name,
                'course_code': result.course.course_code,
                'purpose': 'Revaluation Fee'
            }
        )
        
        if not order_response['success']:
            return order_response
        
        # Create pending revaluation request
        reval_request = RevaluationRequest.objects.create(
            student=student,
            result=result,
            razorpay_order_id=order_response['order_id'],
            amount_paid=config.fee_per_subject,
            status='PENDING'
        )
        
        return {
            'success': True,
            'order_id': order_response['order_id'],
            'amount': config.fee_per_subject,
            'request_id': reval_request.id,
            'receipt_id': receipt_id
        }
    
    def complete_payment(self, order_id, payment_id, signature):
        """
        Complete revaluation payment after Razorpay confirmation.
        
        Args:
            order_id: Razorpay order ID
            payment_id: Razorpay payment ID
            signature: Payment signature
        
        Returns:
            dict: Success status and request details
        """
        from results.models_extended import RevaluationRequest
        
        # Verify signature
        if not self.razorpay.verify_payment_signature(order_id, payment_id, signature):
            return {
                'success': False,
                'error': 'Invalid payment signature'
            }
        
        try:
            # Get revaluation request
            reval_request = RevaluationRequest.objects.get(
                razorpay_order_id=order_id
            )
            
            # Update payment details
            reval_request.razorpay_payment_id = payment_id
            reval_request.razorpay_signature = signature
            reval_request.status = 'PAID'
            reval_request.save()
            
            # Generate receipt (implement separately)
            from results.services.receipt_service import generate_revaluation_receipt
            receipt_url = generate_revaluation_receipt(reval_request)
            reval_request.receipt_url = receipt_url
            reval_request.save()
            
            # Create notification
            from results.signals import create_notification
            create_notification(
                student=reval_request.student,
                notification_type='PAYMENT_SUCCESS',
                title='Revaluation Payment Successful',
                message=f'Your payment for {reval_request.result.course.course_title} revaluation has been received.',
                revaluation_request=reval_request
            )
            
            # Log audit trail
            from results.signals import log_audit
            log_audit(
                action_type='REVALUATION_PAID',
                student=reval_request.student,
                description=f'Revaluation payment completed for {reval_request.result.course.course_code}',
                metadata={
                    'payment_id': payment_id,
                    'amount': float(reval_request.amount_paid),
                    'course': reval_request.result.course.course_code
                }
            )
            
            return {
                'success': True,
                'request': reval_request,
                'receipt_url': receipt_url
            }
        
        except RevaluationRequest.DoesNotExist:
            return {
                'success': False,
                'error': 'Revaluation request not found'
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }


class MakeupExamPaymentService:
    """Service for handling makeup exam payments."""
    
    def __init__(self):
        self.razorpay = RazorpayService()
    
    def create_makeup_exam_order(self, student, subjects, semester, config):
        """
        Create payment order for makeup exam.
        
        Args:
            student: Student instance
            subjects: List of Course instances
            semester: Semester number
            config: MakeupExamConfiguration instance
        
        Returns:
            dict: Order details or error
        """
        from results.models_extended import MakeupExamRequest
        
        # Generate exam cycle ID
        exam_cycle = f"{timezone.now().year}-MAKEUP-SEM{semester}"
        
        # Check for duplicate request
        existing = MakeupExamRequest.objects.filter(
            student=student,
            exam_cycle=exam_cycle,
            status__in=['PENDING', 'PAID', 'ADMIN_VERIFIED', 'PROCTOR_VERIFIED', 'APPROVED']
        ).first()
        
        if existing:
            return {
                'success': False,
                'error': 'You already have a pending makeup exam request for this cycle'
            }
        
        # Calculate total amount
        total_amount = len(subjects) * config.fee_per_subject
        
        # Generate receipt ID
        receipt_id = f"MAKEUP-{student.usn}-SEM{semester}-{timezone.now().strftime('%Y%m%d%H%M%S')}"
        
        # Create Razorpay order
        order_response = self.razorpay.create_order(
            amount=total_amount,
            receipt_id=receipt_id,
            notes={
                'student_usn': student.usn,
                'student_name': student.name,
                'semester': semester,
                'subject_count': len(subjects),
                'purpose': 'Makeup Exam Fee'
            }
        )
        
        if not order_response['success']:
            return order_response
        
        # Create pending makeup exam request
        makeup_request = MakeupExamRequest.objects.create(
            student=student,
            semester=semester,
            exam_cycle=exam_cycle,
            razorpay_order_id=order_response['order_id'],
            amount_paid=total_amount,
            status='PENDING',
            exam_center=config.exam_center,
            exam_date=config.exam_date
        )
        
        # Add subjects
        makeup_request.subjects.set(subjects)
        
        return {
            'success': True,
            'order_id': order_response['order_id'],
            'amount': total_amount,
            'request_id': makeup_request.id,
            'receipt_id': receipt_id,
            'subject_count': len(subjects)
        }
    
    def complete_payment(self, order_id, payment_id, signature):
        """
        Complete makeup exam payment.
        
        Args:
            order_id: Razorpay order ID
            payment_id: Razorpay payment ID
            signature: Payment signature
        
        Returns:
            dict: Success status and request details
        """
        from results.models_extended import MakeupExamRequest
        
        # Verify signature
        if not self.razorpay.verify_payment_signature(order_id, payment_id, signature):
            return {
                'success': False,
                'error': 'Invalid payment signature'
            }
        
        try:
            # Get makeup exam request
            makeup_request = MakeupExamRequest.objects.get(
                razorpay_order_id=order_id
            )
            
            # Update payment details
            makeup_request.razorpay_payment_id = payment_id
            makeup_request.razorpay_signature = signature
            makeup_request.status = 'PAID'
            makeup_request.save()
            
            # Generate receipt
            from results.services.receipt_service import generate_makeup_exam_receipt
            receipt_url = generate_makeup_exam_receipt(makeup_request)
            makeup_request.receipt_url = receipt_url
            makeup_request.save()
            
            # Create notification
            from results.signals import create_notification
            create_notification(
                student=makeup_request.student,
                notification_type='REQUEST_SUBMITTED',
                title='Makeup Exam Registration Successful',
                message=f'Your makeup exam registration for {makeup_request.get_subject_count()} subject(s) has been submitted for verification.',
                makeup_exam_request=makeup_request
            )
            
            # Log audit trail
            from results.signals import log_audit
            log_audit(
                action_type='MAKEUP_PAID',
                student=makeup_request.student,
                description=f'Makeup exam payment completed for {makeup_request.get_subject_count()} subjects',
                metadata={
                    'payment_id': payment_id,
                    'amount': float(makeup_request.amount_paid),
                    'exam_cycle': makeup_request.exam_cycle
                }
            )
            
            return {
                'success': True,
                'request': makeup_request,
                'receipt_url': receipt_url
            }
        
        except MakeupExamRequest.DoesNotExist:
            return {
                'success': False,
                'error': 'Makeup exam request not found'
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
