"""
Views for Student Results System.
"""

# Standard Library
import os
from datetime import datetime
from decimal import Decimal

# Third-Party
from dotenv import load_dotenv
from django_ratelimit.decorators import ratelimit

# Django Core
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Q, Avg, Count
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

# Local App Imports
from .models import (
    Student,
    StudentMetadata,
    Course,
    Result,
    UploadHistory,
    RevaluationConfiguration,
    RevaluationRequest,
    MakeupExamConfiguration,
    MakeupExamRequest,
    StudentNotification,
    AuditLog,
    Paper_Seeing,
    PaperSeeingConfiguration,
    PaperSeeingRequest
)

from .forms import (
    ResultQueryForm,
    BulkUploadForm,
    ResultEditForm
)

from .utils import process_results_excel, process_metadata_excel
from .pdf_generator import generate_result_pdf

from .services.payment_service import (
    RevaluationPaymentService,
    PaperSeeingPaymentService,
    MakeupExamPaymentService
)

from .services.hall_ticket_service import generate_hall_ticket_pdf

load_dotenv()

def admin_panel(request):
    is_proctor = request.user.groups.filter(name='Proctor').exists()
    is_admin = request.user.is_superuser
    return render(request, 'admin_panel/dashboard.html', {
        'is_proctor': is_proctor,
        'is_admin': is_admin,
    })

def is_staff_or_professor(user):
    """Check if user is staff or superuser."""
    return user.is_staff or user.is_superuser

def is_proctor(user):
    """Check if user has proctor role."""
    return user.groups.filter(name='Proctor').exists() or user.is_superuser

def get_failed_subjects(student, semester):
    """Get all failed subjects for a student in a semester."""
    return Result.objects.filter(
        student=student,
        semester=semester,
        final_cie_marks__lt=40  # Fail threshold
    ).select_related('course')


@ratelimit(key='ip', rate='10/m', method='POST')
@ratelimit(key='ip', rate='10/m', method='POST')
def home(request):
    """Home page with result query form - ENHANCED VERSION."""
    context = {
        'RECAPTCHA_SITE_KEY': os.getenv("RECAPTCHA_SITE_KEY"),        
        'form': ResultQueryForm(),
        'show_skeleton': False,
        'error_message': None,
        'results': None
    }
    
    if request.method == 'POST':
        form = ResultQueryForm(request.POST)
        
        if form.is_valid():
            # Verify reCAPTCHA (skip if disabled)
            recaptcha_response = request.POST.get('g-recaptcha-response', '')
            if os.getenv("RECAPTCHA_SECRET_KEY"):  # Only verify if configured
                if not form.verify_recaptcha(recaptcha_response):
                    context['error_message'] = 'reCAPTCHA verification failed. Please try again.'
                    context['form'] = form
                    return render(request, 'results/home.html', context)
            
            usn = form.cleaned_data['usn']
            dob = form.cleaned_data['dob']
            semester = form.cleaned_data['semester']
            
            # Check if student exists
            try:
                student = Student.objects.get(usn=usn)
                
                # Verify DOB
                try:
                    metadata = student.metadata
                    if metadata.dob != dob:
                        context['error_message'] = 'DOB provided is wrong according to USN provided'
                        context['form'] = form
                        return render(request, 'results/home.html', context)
                except StudentMetadata.DoesNotExist:
                    context['error_message'] = 'Student metadata not found'
                    context['form'] = form
                    return render(request, 'results/home.html', context)
                
                # Fetch results for the semester
                results = Result.objects.filter(
                    student=student,
                    semester=semester
                ).select_related('course').order_by('course__course_code')
                
                if not results.exists():
                    context['error_message'] = f'No results found for Semester {semester}'
                    context['form'] = form
                    return render(request, 'results/home.html', context)
                
                # ===== NEW: Get revaluation configuration =====
                try:
                    reval_config = RevaluationConfiguration.objects.first()
                    paperseeing_config = PaperSeeingConfiguration.objects.first()
                except:
                    reval_config = None
                    paperseeing_config = None
                
                # ===== NEW: Check revaluation status for each result =====
                results_with_reval_and_paperseeing = []
                for result in results:
                    existing_reval = None
                    can_request_reval = False
                    
                    try:
                        # Check if revaluation already requested
                        existing_reval = RevaluationRequest.objects.filter(
                            student=student,
                            result=result
                        ).first()
                        
                        # Can request if window open and no existing request
                        if reval_config and reval_config.is_active() and not existing_reval:
                            can_request_reval = True
                    except:
                        pass
                    
                    can_request_paperseeing = False
                    existing_paperseeing = None
                    try:
                        # Check if paperseeing already requested
                        existing_paperseeing = PaperSeeingRequest.objects.filter(
                            student=student,
                            result=result
                        ).first()
                        
                        # Can request if window open and no existing request
                        if paperseeing_config and paperseeing_config.is_active() and not existing_paperseeing:
                            can_request_paperseeing = True
                    except:
                        pass

                    results_with_reval_and_paperseeing.append({
                        'result': result,
                        'can_request_reval': can_request_reval,
                        'reval_status': existing_reval.status if existing_reval else None,
                        'reval_request': existing_reval,
                        'can_request_paperseeing': can_request_paperseeing,
                        'paperseeing_status': existing_paperseeing.status if existing_paperseeing else None,
                        'paperseeing_request': existing_paperseeing
                    })
                
                # ===== NEW: Check for failed subjects (makeup exam eligibility) =====
                failed_count = results.filter(final_cie_marks__lt=40).count()
                show_makeup_tab = failed_count > 0
                
                # Calculate statistics
                total_marks = sum([r.final_cie_marks for r in results if r.final_cie_marks])
                avg_marks = total_marks / results.count() if results.count() > 0 else 0
                
                # ===== MODIFIED: Enhanced context with new features =====
                context = {
                    'student': student,
                    'metadata': metadata,
                    'results': results,  # Keep for backward compatibility
                    'results_with_reval_and_paperseeing': results_with_reval_and_paperseeing    ,  # NEW: Enhanced results
                    'semester': semester,
                    'total_marks': total_marks,
                    'avg_marks': round(avg_marks, 2),
                    'show_results': True,
                    
                    # NEW: Revaluation feature
                    'reval_config': reval_config,

                    #NEW: Paper Seeing Feature
                    'paperseeing_config': paperseeing_config,
                    'results_with_paperseeing': results_with_reval_and_paperseeing,
                    
                    # NEW: Makeup exam feature
                    'show_makeup_tab': show_makeup_tab,
                    'failed_count': failed_count,
                }
                
                # ===== Use enhanced template (or keep existing) =====
                # Option 1: Use new template with tabs
                return render(request, 'results/result_view_extended.html', context)
                
                # Option 2: Keep using existing template (will still work)
                # return render(request, 'results/result_view.html', context)
                
            except Student.DoesNotExist:
                context['error_message'] = 'Invalid USN'
                context['form'] = form
                return render(request, 'results/home.html', context)
        else:
            context['form'] = form
            context['error_message'] = 'Please correct the errors below'
    
    return render(request, 'results/home.html', context)

def get_failed_subjects(student, semester):
    """Get all failed subjects for a student in a semester."""
    return Result.objects.filter(
        student=student,
        semester=semester,
        final_cie_marks__lt=40  # Fail threshold
    ).select_related('course')

@ratelimit(key='ip', rate='5/m', method='GET')
def download_pdf(request, usn, semester):
    """Generate and download PDF of student results."""
    try:
        student = get_object_or_404(Student, usn=usn)
        metadata = student.metadata
        results = Result.objects.filter(
            student=student,
            semester=semester
        ).select_related('course').order_by('course__course_code')
        
        if not results.exists():
            messages.error(request, 'No results found')
            return redirect('home')
        
        # Generate PDF
        pdf_buffer = generate_result_pdf(student, metadata, results, semester)
        
        # Return PDF response
        response = HttpResponse(pdf_buffer.getvalue(), content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="results_{usn}_sem{semester}.pdf"'
        
        return response
        
    except Exception as e:
        messages.error(request, f'Error generating PDF: {str(e)}')
        return redirect('home')



@login_required
@user_passes_test(is_staff_or_professor)
def admin_dashboard(request):
    """
    Enhanced admin dashboard with all statistics and quick actions.
    """
    # Existing statistics
    total_students = Student.objects.count()
    total_results = Result.objects.count()
    total_courses = Course.objects.count()
    
    # NEW: Extended statistics
    try:
        revaluation_count = RevaluationRequest.objects.count()
        pending_revaluation = RevaluationRequest.objects.filter(
            status__in=['PAID', 'PROCESSING']
        ).count()
        completed_revaluation = RevaluationRequest.objects.filter(status='COMPLETED').count()
        
        makeup_exam_count = MakeupExamRequest.objects.count()
        pending_admin_verification = MakeupExamRequest.objects.filter(
            status='PAID', 
            admin_verified=False
        ).count()
        pending_proctor_verification = MakeupExamRequest.objects.filter(
            admin_verified=True,
            proctor_verified=False
        ).count()
        approved_makeup = MakeupExamRequest.objects.filter(status='APPROVED').count()
        
        unread_notifications = StudentNotification.objects.filter(is_read=False).count()
        recent_actions = AuditLog.objects.all()[:10]
        
    except:
        revaluation_count = 0
        pending_revaluation = 0
        completed_revaluation = 0
        makeup_exam_count = 0
        pending_admin_verification = 0
        pending_proctor_verification = 0
        approved_makeup = 0
        unread_notifications = 0
        recent_actions = []
    
    # Recent uploads
    recent_uploads = UploadHistory.objects.all()[:5]
    
    # Quick stats
    failed_students = Result.objects.filter(final_cie_marks__lt=40).values('student').distinct().count()
    
    context = {
        # Existing
        'total_students': total_students,
        'total_results': total_results,
        'total_courses': total_courses,
        'recent_uploads': recent_uploads,
        
        # NEW: Revaluation stats
        'revaluation_count': revaluation_count,
        'pending_revaluation': pending_revaluation,
        'completed_revaluation': completed_revaluation,
        
        # NEW: Makeup exam stats
        'makeup_exam_count': makeup_exam_count,
        'pending_admin_verification': pending_admin_verification,
        'pending_proctor_verification': pending_proctor_verification,
        'approved_makeup': approved_makeup,
        
        # NEW: Other stats
        'failed_students': failed_students,
        'unread_notifications': unread_notifications,
        'recent_actions': recent_actions,
        'is_admin': request.user.is_superuser,
    }
    
    return render(request, 'admin_panel/dashboard.html', context)



@login_required
@user_passes_test(is_staff_or_professor)
def bulk_upload(request):
    """Handle bulk Excel/CSV upload."""
    if request.method == 'POST':
        form = BulkUploadForm(request.POST, request.FILES)
        
        if form.is_valid():
            upload_type = form.cleaned_data['upload_type']
            uploaded_file = request.FILES['file']
            
            # Save file temporarily
            file_path = os.path.join('media', 'uploads', uploaded_file.name)
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            
            with open(file_path, 'wb+') as destination:
                for chunk in uploaded_file.chunks():
                    destination.write(chunk)
            
            try:
                # Process file based on type
                if upload_type == 'results':
                    stats = process_results_excel(file_path, request.user)
                else:
                    stats = process_metadata_excel(file_path, request.user)
                
                messages.success(
                    request,
                    f'Upload successful! Processed: {stats["processed"]}, '
                    f'Created: {stats["created"]}, Updated: {stats["updated"]}, '
                    f'Skipped: {stats["skipped"]}'
                )
                
                if stats.get('errors'):
                    messages.warning(request, f'Errors: {len(stats["errors"])} rows had issues')
                
            except Exception as e:
                messages.error(request, f'Upload failed: {str(e)}')
            
            finally:
                # Clean up temporary file
                if os.path.exists(file_path):
                    os.remove(file_path)
            
            return redirect('admin_panel')
    else:
        form = BulkUploadForm()
    
    return render(request, 'admin_panel/bulk_upload.html', {'form': form})


@login_required
@user_passes_test(is_staff_or_professor)
def edit_result(request, result_id):
    """Edit individual result marks."""
    result = get_object_or_404(Result, id=result_id)
    
    if request.method == 'POST':
        form = ResultEditForm(request.POST, instance=result)
        if form.is_valid():
            form.save()
            messages.success(request, 'Result updated successfully')
            return redirect('admin_panel')
    else:
        form = ResultEditForm(instance=result)
    
    context = {
        'form': form,
        'result': result,
        'student': result.student,
        'course': result.course
    }
    
    return render(request, 'admin_panel/edit_result.html', context)


@login_required
@user_passes_test(is_staff_or_professor)
def search_students(request):
    """Search students with autocomplete."""
    query = request.GET.get('q', '').strip()
    
    if len(query) < 2:
        return JsonResponse({'results': []})
    
    students = Student.objects.filter(
        Q(usn__icontains=query) |
        Q(name__icontains=query)
    )[:10]
    
    results = [{
        'usn': s.usn,
        'name': s.name,
        'department': s.department or 'N/A'
    } for s in students]
    
    return JsonResponse({'results': results})


@login_required
@user_passes_test(is_staff_or_professor)
def analytics(request):
    """Detailed analytics page."""
    # Filter parameters
    semester = request.GET.get('semester')
    admission_route = request.GET.get('admission_route')
    course_id = request.GET.get('course')
    
    # Base queryset
    results = Result.objects.select_related('student', 'course', 'student__metadata')
    
    # Apply filters
    if semester:
        results = results.filter(semester=semester)
    if admission_route:
        results = results.filter(student__metadata__admission_route=admission_route)
    if course_id:
        results = results.filter(course_id=course_id)
    
    # Calculate statistics
    total_results = results.count()
    avg_marks = results.aggregate(Avg('final_cie_marks'))['final_cie_marks__avg'] or 0
    
    # Top performers
    top_students = results.values(
        'student__usn', 'student__name'
    ).annotate(
        avg_marks=Avg('final_cie_marks')
    ).order_by('-avg_marks')[:10]
    
    # Course-wise performance
    course_stats = results.values(
        'course__course_code', 'course__course_title'
    ).annotate(
        avg_marks=Avg('final_cie_marks'),
        count=Count('id')
    ).order_by('-avg_marks')
    
    context = {
        'total_results': total_results,
        'avg_marks': round(avg_marks, 2),
        'top_students': top_students,
        'course_stats': course_stats,
        'courses': Course.objects.all(),
        'selected_semester': semester,
        'selected_route': admission_route,
        'selected_course': course_id,
    }
    
    return render(request, 'admin_panel/analytics.html', context)

"""
Views for Revaluation and Makeup Exam features.

LOCATION: results/views_extended.py

Add these to your existing results/views.py or import them.
"""



# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

# ============================================================================
# STUDENT RESULT VIEW WITH REVALUATION BUTTON
# ============================================================================

@ratelimit(key='ip', rate='20/m', method='GET')
def student_result_view_extended(request, usn, semester):
    """
    Extended result view with revaluation options.
    This enhances the existing result_view.
    """
    try:
        student = get_object_or_404(Student, usn=usn)
        results = Result.objects.filter(
            student=student,
            semester=semester
        ).select_related('course').order_by('course__course_code')
        
        if not results.exists():
            messages.error(request, f'No results found for Semester {semester}')
            return redirect('home')
        
        # Get revaluation configuration
        reval_config = RevaluationConfiguration.objects.first()
        
        # Check which subjects can be revaluated
        results_with_reval = []
        for result in results:
            # Check if revaluation already requested
            existing_reval = RevaluationRequest.objects.filter(
                student=student,
                result=result
            ).first()
            
            results_with_reval.append({
                'result': result,
                'can_request_reval': reval_config and reval_config.is_active() and not existing_reval,
                'reval_status': existing_reval.status if existing_reval else None,
                'reval_request': existing_reval
            })
        
        # Get failed subjects count for makeup exam tabstudent_result_view_extended
        failed_count = results.filter(final_cie_marks__lt=40).count()
        
        # Calculate statistics
        total_marks = sum([r.final_cie_marks for r in results if r.final_cie_marks])
        avg_marks = total_marks / results.count() if results.count() > 0 else 0
        
        context = {
            'student': student,
            'metadata': student.metadata,
            'results_with_reval': results_with_reval,
            'semester': semester,
            'total_marks': total_marks,
            'avg_marks': round(avg_marks, 2),
            'reval_config': reval_config,
            'show_makeup_tab': failed_count > 0,
            'failed_count': failed_count,
        }
        
        return render(request, 'results/result_view_extended.html', context)
        
    except Exception as e:
        messages.error(request, f'Error loading results: {str(e)}')
        return redirect('home')


# ============================================================================
# REVALUATION REQUEST VIEWS
# ============================================================================

@ratelimit(key='ip', rate='10/m', method='POST')
@require_http_methods(["POST"])
def create_revaluation_order(request):
    """Create Razorpay order for revaluation."""
    try:
        result_id = request.POST.get('result_id')
        result = get_object_or_404(Result, id=result_id)
        student = result.student
        
        # Get configuration
        config = RevaluationConfiguration.objects.first()
        if not config or not config.is_active():
            return JsonResponse({
                'success': False,
                'error': 'Revaluation window is currently closed'
            })
        
        # Create payment order
        payment_service = RevaluationPaymentService()
        order_response = payment_service.create_revaluation_order(
            student=student,
            result=result,
            config=config
        )
        
        if order_response['success']:
            # Return Razorpay order details for frontend
            return JsonResponse({
                'success': True,
                'order_id': order_response['order_id'],
                'amount': float(order_response['amount']),
                'currency': 'INR',
                'razorpay_key': os.getenv("RAZORPAY_KEY_ID"),
                'student_name': student.name,
                'student_email': student.metadata.email if hasattr(student.metadata, 'email') else '',
                'student_contact': student.metadata.phone if hasattr(student.metadata, 'phone') else ''
            })
        else:
            return JsonResponse(order_response, status=400)
    
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@ratelimit(key='ip', rate='10/m', method='POST')
@require_http_methods(["POST"])
def verify_revaluation_payment(request):
    """Verify and complete revaluation payment."""
    try:
        order_id = request.POST.get('razorpay_order_id')
        payment_id = request.POST.get('razorpay_payment_id')
        signature = request.POST.get('razorpay_signature')
        
        if not all([order_id, payment_id, signature]):
            return JsonResponse({
                'success': False,
                'error': 'Missing payment details'
            }, status=400)
        
        # Complete payment
        payment_service = RevaluationPaymentService()
        result = payment_service.complete_payment(order_id, payment_id, signature)
        
        if result['success']:
            return JsonResponse({
                'success': True,
                'message': 'Payment successful! Your revaluation request has been submitted.',
                'receipt_url': result['receipt_url']
            })
        else:
            return JsonResponse(result, status=400)
    
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@ratelimit(key='ip', rate='10/m', method='POST')
@require_http_methods(["POST"])
def create_paper_seeing_order(request):
    """Create Razorpay order for paper_seeing."""
    try:
        result_id = request.POST.get('result_id')
        result = get_object_or_404(Result, id=result_id)
        student = result.student
        
        # Get configuration
        config = PaperSeeingConfiguration.objects.first()
        if not config or not config.is_active():
            return JsonResponse({
                'success': False,
                'error': 'Paper Seeing window is currently closed'
            })
        
        # Create payment order
        payment_service = PaperSeeingPaymentService()
        order_response = payment_service.create_PaperSeeing_order(
            student=student,
            result=result,
            config=config
        )
        
        if order_response['success']:
            # Return Razorpay order details for frontend
            return JsonResponse({
                'success': True,
                'order_id': order_response['order_id'],
                'amount': float(order_response['amount']),
                'currency': 'INR',
                'razorpay_key': os.getenv("RAZORPAY_KEY_ID"),
                'student_name': student.name,
                'student_email': student.metadata.email if hasattr(student.metadata, 'email') else '',
                'student_contact': student.metadata.phone if hasattr(student.metadata, 'phone') else ''
            })
        else:
            return JsonResponse(order_response, status=400)
    
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@ratelimit(key='ip', rate='10/m', method='POST')
@require_http_methods(["POST"])
def verify_paperseeing_payment(request):
    """Verify and complete paperseeing payment."""
    try:
        order_id = request.POST.get('razorpay_order_id')
        payment_id = request.POST.get('razorpay_payment_id')
        signature = request.POST.get('razorpay_signature')
        
        if not all([order_id, payment_id, signature]):
            return JsonResponse({
                'success': False,
                'error': 'Missing payment details'
            }, status=400)
        
        # Complete payment
        payment_service = PaperSeeingPaymentService()
        result = payment_service.complete_payment(order_id, payment_id, signature)
        
        if result['success']:
            return JsonResponse({
                'success': True,
                'message': 'Payment successful! Your paperseeing request has been submitted.',
                'receipt_url': result['receipt_url']
            })
        else:
            return JsonResponse(result, status=400)
    
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


# ============================================================================
# MAKEUP EXAM VIEWS
# ============================================================================

# @ratelimit(key='ip', rate='20/m', method='GET')
# def makeup_exam_page(request, usn, semester):
#     """Display makeup exam registration page for failed subjects."""
#     try:
#         student = get_object_or_404(Student, usn=usn)
        
#         # Get failed subjects
#         failed_results = get_failed_subjects(student, semester)
        
#         if not failed_results.exists():
#             messages.info(request, 'You have no failed subjects.')
#             return redirect('student_result_view_extended', usn=usn, semester=semester)
        
#         # Get configurationMakeupExamRequest
#         config = MakeupExamConfiguration.objects.first()
        
#         # Check for existing request
#         existing_request = MakeupExamRequest.objects.filter(
#             student=student,
#             semester=semester,
#             status__in=['PENDING', 'PAID', 'ADMIN_VERIFIED', 'PROCTOR_VERIFIED', 'APPROVED']
#         ).first()
        
#         context = {
#             'student': student,
#             'semester': semester,
#             'failed_results': failed_results,
#             'config': config,
#             'existing_request': existing_request,
#             'can_register': config and config.is_active() and not existing_request,
#         }
        
#         return render(request, 'results/makeup_exam.html', context)
        
#     except Exception as e:
#         messages.error(request, f'Error: {str(e)}')
#         return redirect('home')


# @ratelimit(key='ip', rate='10/m', method='POST')
# @require_http_methods(["POST"])
# def create_makeup_exam_order(request):
#     """Create Razorpay order for makeup exam registration."""
#     try:
#         usn = request.POST.get('usn')
#         semester = int(request.POST.get('semester'))
#         subject_ids = request.POST.getlist('subjects[]')
        
#         student = get_object_or_404(Student, usn=usn)
        
#         # Validate subjects
#         subjects = Course.objects.filter(id__in=subject_ids)
        
#         if not subjects.exists():
#             return JsonResponse({
#                 'success': False,
#                 'error': 'No subjects selected'
#             }, status=400)
        
#         # Get configuration
#         config = MakeupExamConfiguration.objects.first()
#         if not config or not config.is_active():
#             return JsonResponse({
#                 'success': False,
#                 'error': 'Makeup exam registration is currently closed'
#             })
        
#         # Validate that selected subjects are actually failed
#         failed_subject_ids = get_failed_subjects(student, semester).values_list('course_id', flat=True)
#         invalid_subjects = [s.id for s in subjects if s.id not in failed_subject_ids]
        
#         if invalid_subjects:
#             return JsonResponse({
#                 'success': False,
#                 'error': 'You can only register for failed subjects'
#             }, status=400)
        
#         # Create payment order
#         payment_service = MakeupExamPaymentService()
#         order_response = payment_service.create_makeup_exam_order(
#             student=student,
#             subjects=list(subjects),
#             semester=semester,
#             config=config
#         )
        
#         if order_response['success']:
#             return JsonResponse({
#                 'success': True,
#                 'order_id': order_response['order_id'],
#                 'amount': float(order_response['amount']),
#                 'currency': 'INR',
#                 'razorpay_key': os.getenv("RAZORPAY_KEY_ID"),
#                 'student_name': student.name,
#                 'subject_count': order_response['subject_count']
#             })
#         else:
#             return JsonResponse(order_response, status=400)
    
#     except Exception as e:
#         return JsonResponse({
#             'success': False,
#             'error': str(e)
#         }, status=500)


# @ratelimit(key='ip', rate='10/m', method='POST')
# @require_http_methods(["POST"])
# def verify_makeup_exam_payment(request):
#     """Verify and complete makeup exam payment."""
#     try:
#         order_id = request.POST.get('razorpay_order_id')
#         payment_id = request.POST.get('razorpay_payment_id')
#         signature = request.POST.get('razorpay_signature')
        
#         if not all([order_id, payment_id, signature]):
#             return JsonResponse({
#                 'success': False,
#                 'error': 'Missing payment details'
#             }, status=400)
        
#         # Complete payment
#         payment_service = MakeupExamPaymentService()
#         result = payment_service.complete_payment(order_id, payment_id, signature)
        
#         if result['success']:
#             return JsonResponse({
#                 'success': True,
#                 'message': 'Payment successful! Your makeup exam registration has been submitted for verification.',
#                 'receipt_url': result['receipt_url']
#             })
#         else:
#             return JsonResponse(result, status=400)
    
#     except Exception as e:
#         return JsonResponse({
#             'success': False,
#             'error': str(e)
#         }, status=500)


# ============================================================================
# ADMIN VERIFICATION VIEWS
# ============================================================================

@login_required
@user_passes_test(is_staff_or_professor)
def admin_revaluation_requests(request):
    """Admin view for managing revaluation requests."""
    # Filters
    status_filter = request.GET.get('status', '')
    search = request.GET.get('search', '')
    
    requests_qs = RevaluationRequest.objects.select_related(
        'student', 'result__course'
    ).order_by('-created_at')
    
    if status_filter:
        requests_qs = requests_qs.filter(status=status_filter)
    
    if search:
        requests_qs = requests_qs.filter(
            Q(student__usn__icontains=search) |
            Q(student__name__icontains=search) |
            Q(result__course__course_code__icontains=search)
        )
    
    # Statistics
    stats = {
        'total': RevaluationRequest.objects.count(),
        'pending': RevaluationRequest.objects.filter(status='PAID').count(),
        'processing': RevaluationRequest.objects.filter(status='PROCESSING').count(),
        'completed': RevaluationRequest.objects.filter(status='COMPLETED').count(),
    }
    
    context = {
        'requests': requests_qs,
        'stats': stats,
        'status_filter': status_filter,
        'search': search,
        'is_admin': request.user.is_superuser,
    }
    
    return render(request, 'admin_panel/revaluation_requests.html', context)

@login_required
@user_passes_test(is_staff_or_professor)
def admin_search_requests(request):
    """Admin view for managing revaluation requests."""
    # Filters
    # status_filter = request.GET.get('status', '')
    search = request.GET.get('search', '')
    
    requests_qs = Student.objects.order_by('-created_at')
    
    # if status_filter:
    #     requests_qs = requests_qs.filter(status=status_filter)
    
    if search:
        requests_qs = requests_qs.filter(
            Q(usn__icontains=search) |
            Q(name__icontains=search)
        )
    
    # # Statistics
    # stats = {
    #     'total': RevaluationRequest.objects.count(),
    #     'pending': RevaluationRequest.objects.filter(status='PAID').count(),
    #     'processing': RevaluationRequest.objects.filter(status='PROCESSING').count(),
    #     'completed': RevaluationRequest.objects.filter(status='COMPLETED').count(),
    # }
    
    context = {
        'requests': requests_qs,
        # 'stats': stats,
        # 'status_filter': status_filter,
        'search': search,
        'is_admin': request.user.is_superuser,
    }
    
    return render(request, 'admin_panel/student_search.html', context)


@login_required
@user_passes_test(is_staff_or_professor)
def admin_student_list_requests(request):
    """Admin view for managing revaluation requests."""
    # Filters
    # status_filter = request.GET.get('status', '')
    search = request.GET.get('search', '')
    
    requests_qs = Student.objects.order_by('-created_at')
    
    # if status_filter:
    #     requests_qs = requests_qs.filter(status=status_filter)
    
    if search:
        requests_qs = requests_qs.filter(
            Q(usn__icontains=search) |
            Q(name__icontains=search)
        )
    
    # # Statistics
    # stats = {
    #     'total': RevaluationRequest.objects.count(),
    #     'pending': RevaluationRequest.objects.filter(status='PAID').count(),
    #     'processing': RevaluationRequest.objects.filter(status='PROCESSING').count(),
    #     'completed': RevaluationRequest.objects.filter(status='COMPLETED').count(),
    # }
    
    context = {
        'requests': requests_qs,
        # 'stats': stats,
        # 'status_filter': status_filter,
        'search': search,
        'is_admin': request.user.is_superuser,
    }
    
    return render(request, 'admin_panel/student_list.html', context)


@login_required
@user_passes_test(is_staff_or_professor)
def admin_paperseeing_requests(request):
    """Admin view for managing paperseeing requests."""
    # Filters
    status_filter = request.GET.get('status', '')
    search = request.GET.get('search', '')
    
    requests_qs = PaperSeeingRequest.objects.select_related(
        'student', 'result__course'
    ).order_by('-created_at')
    
    if status_filter:
        requests_qs = requests_qs.filter(status=status_filter)
    
    if search:
        requests_qs = requests_qs.filter(
            Q(student__usn__icontains=search) |
            Q(student__name__icontains=search) |
            Q(result__course__course_code__icontains=search)
        )
    
    # Statistics
    stats = {
        'total': PaperSeeingRequest.objects.count(),
        'pending': PaperSeeingRequest.objects.filter(status='PAID').count(),
        'processing': PaperSeeingRequest.objects.filter(status='PROCESSING').count(),
        'completed': PaperSeeingRequest.objects.filter(status='COMPLETED').count(),
    }
    
    context = {
        'requests': requests_qs,
        'stats': stats,
        'status_filter': status_filter,
        'search': search,
        'is_admin': request.user.is_superuser,
    }
    
    return render(request, 'admin_panel/paperseeing_requests.html', context)


@login_required
@user_passes_test(is_staff_or_professor)
def admin_makeup_exam_requests(request):
    """Admin view for managing makeup exam requests."""
    # Filters
    status_filter = request.GET.get('status', '')
    search = request.GET.get('search', '')
    
    requests_qs = MakeupExamRequest.objects.prefetch_related('subjects').select_related(
        'student'
    ).order_by('-created_at')
    
    if status_filter:
        requests_qs = requests_qs.filter(status=status_filter)
    
    if search:
        requests_qs = requests_qs.filter(
            Q(student__usn__icontains=search) |
            Q(student__name__icontains=search)
        )
    
    # Statistics
    stats = {
        'total': MakeupExamRequest.objects.count(),
        'paid': MakeupExamRequest.objects.filter(status='PAID').count(),
        'admin_verified': MakeupExamRequest.objects.filter(admin_verified=True).count(),
        'proctor_verified': MakeupExamRequest.objects.filter(proctor_verified=True).count(),
        'approved': MakeupExamRequest.objects.filter(status='APPROVED').count(),
    }
    
    context = {
        'requests': requests_qs,
        'stats': stats,
        'status_filter': status_filter,
        'search': search,
    }
    
    return render(request, 'admin_panel/makeup_exam_requests.html', context)


@login_required
@user_passes_test(is_staff_or_professor)
@require_http_methods(["POST"])
def admin_verify_makeup_request(request, request_id):
    """Admin verification of makeup exam request."""
    try:
        makeup_request = get_object_or_404(MakeupExamRequest, id=request_id)
        
        action = request.POST.get('action')  # 'approve' or 'reject'
        remarks = request.POST.get('remarks', '')
        
        if action == 'approve':
            makeup_request.admin_verified = True
            makeup_request.admin_verified_by = request.user
            makeup_request.admin_verified_at = timezone.now()
            makeup_request.admin_remarks = remarks
            
            # Update status if proctor also verified
            if makeup_request.proctor_verified:
                makeup_request.status = 'APPROVED'
            else:
                makeup_request.status = 'ADMIN_VERIFIED'
            
            makeup_request.save()
            
            messages.success(request, 'Request approved successfully')
            
            # Create notification
            from results.signals import create_notification
            create_notification(
                student=makeup_request.student,
                notification_type='ADMIN_VERIFIED',
                title='Makeup Exam Request Verified by Admin',
                message='Your makeup exam registration has been verified by the admin.',
                makeup_exam_request=makeup_request
            )
            
        elif action == 'reject':
            makeup_request.status = 'REJECTED'
            makeup_request.admin_remarks = remarks
            makeup_request.save()
            
            messages.success(request, 'Request rejected')
            
            # Notification for rejection
            from results.signals import create_notification
            create_notification(
                student=makeup_request.student,
                notification_type='REQUEST_REJECTED',
                title='Makeup Exam Request Rejected',
                message=f'Your makeup exam registration has been rejected. Reason: {remarks}',
                makeup_exam_request=makeup_request
            )
        
        return redirect('admin_makeup_exam_requests')
    
    except Exception as e:
        messages.error(request, f'Error: {str(e)}')
        return redirect('admin_makeup_exam_requests')


# ============================================================================
# PROCTOR VERIFICATION VIEWS
# ============================================================================

@login_required
@user_passes_test(is_proctor)
def proctor_makeup_exam_requests(request):
    """Proctor view for verifying makeup exam requests."""
    # Only show admin-verified requests
    requests_qs = MakeupExamRequest.objects.filter(
        admin_verified=True,
        proctor_verified=False
    ).prefetch_related('subjects').select_related('student').order_by('-created_at')
    
    context = {
        'requests': requests_qs,
    }
    
    return render(request, 'proctor/makeup_exam_verification.html', context)


@login_required
@user_passes_test(is_proctor)
@require_http_methods(["POST"])
def proctor_verify_makeup_request(request, request_id):
    """Proctor verification of makeup exam request."""
    try:
        makeup_request = get_object_or_404(MakeupExamRequest, id=request_id)
        
        if not makeup_request.admin_verified:
            messages.error(request, 'Admin verification required first')
            return redirect('proctor_makeup_exam_requests')
        
        action = request.POST.get('action')
        remarks = request.POST.get('remarks', '')
        
        if action == 'approve':
            makeup_request.proctor_verified = True
            makeup_request.proctor_verified_by = request.user
            makeup_request.proctor_verified_at = timezone.now()
            makeup_request.proctor_remarks = remarks
            makeup_request.status = 'APPROVED'
            makeup_request.save()
            
            messages.success(request, 'Request approved - Hall ticket generation enabled')
            
            # Create notification
            from results.signals import create_notification
            create_notification(
                student=makeup_request.student,
                notification_type='HALL_TICKET_READY',
                title='Hall Ticket Ready for Download',
                message='Your makeup exam hall ticket is now ready for download.',
                makeup_exam_request=makeup_request
            )
        
        return redirect('proctor_makeup_exam_requests')
    
    except Exception as e:
        messages.error(request, f'Error: {str(e)}')
        return redirect('proctor_makeup_exam_requests')


# ============================================================================
# HALL TICKET GENERATION
# ============================================================================

@ratelimit(key='ip', rate='10/m', method='GET')
def download_hall_ticket(request, request_id):
    """Generate and download makeup exam hall ticket."""
    try:
        makeup_request = get_object_or_404(MakeupExamRequest, id=request_id)
        
        # Verify eligibility
        if not makeup_request.can_generate_hall_ticket():
            messages.error(request, 'Hall ticket not yet available')
            return redirect('home')
        
        # Generate PDF
        pdf_buffer = generate_hall_ticket_pdf(makeup_request)
        
        # Return PDF
        response = HttpResponse(pdf_buffer.getvalue(), content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="hall_ticket_{makeup_request.student.usn}.pdf"'
        
        return response
        
    except Exception as e:
        messages.error(request, f'Error generating hall ticket: {str(e)}')
        return redirect('home')
    
@ratelimit(key='ip', rate='10/m', method='GET')
def download_receipt(request, receipt_type, request_id):
    """
    Download receipt PDF for revaluation or makeup exam.
    
    Args:
        receipt_type: 'revaluation' or 'makeup'
        request_id: ID of the request
    """
    try:
        if receipt_type == 'revaluation':
            reval_request = get_object_or_404(RevaluationRequest, id=request_id)
            
            if not reval_request.receipt_url:
                messages.error(request, 'Receipt not available')
                return redirect('home')
            
            # Redirect to receipt URL
            return redirect(reval_request.receipt_url)
            
        elif receipt_type == 'makeup':
            makeup_request = get_object_or_404(MakeupExamRequest, id=request_id)
            
            if not makeup_request.receipt_url:
                messages.error(request, 'Receipt not available')
                return redirect('home')
            
            # Redirect to receipt URL
            return redirect(makeup_request.receipt_url)
        
        else:
            messages.error(request, 'Invalid receipt type')
            return redirect('home')
            
    except Exception as e:
        messages.error(request, f'Error downloading receipt: {str(e)}')
        return redirect('home')

# ============================================================================
# PART 2: New Views for Edit Marks and Student Receipts
# Add these to results/views.py
# ============================================================================

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.http import HttpResponse
from django.utils import timezone
from .models import Student, Result, RevaluationRequest, MakeupExamRequest, PaperSeeingRequest


# ============================================================================
# EDIT REVALUATION MARKS VIEW
# ============================================================================

@login_required
@user_passes_test(is_staff_or_professor)
def admin_edit_revaluation(request, result_id):
    """
    Edit marks for a revaluation request.
    Updates both Result and RevaluationRequest models.
    """
    result = get_object_or_404(Result, id=result_id)
    
    # Get revaluation request
    try:
        reval_request = RevaluationRequest.objects.get(result=result)
    except RevaluationRequest.DoesNotExist:
        messages.error(request, 'No revaluation request found for this result.')
        return redirect('admin:results_revaluationrequest_changelist')
    
    if request.method == 'POST':
        try:
            # Get new marks from form
            new_marks = float(request.POST.get('revalued_marks'))
            admin_remarks = request.POST.get('admin_remarks', '')
            
            # Validate marks
            if new_marks < 0 or new_marks > 100:
                messages.error(request, 'Marks must be between 0 and 100.')
                return redirect('admin_edit_revaluation', result_id=result_id)
            
            # Store original marks if not already stored
            if not reval_request.original_marks:
                reval_request.original_marks = result.final_cie_marks
            
            # Check if marks changed
            marks_changed = (new_marks != reval_request.original_marks)
            
            # Update Result model (this updates the actual result)
            old_marks = result.final_cie_marks
            result.final_cie_marks = new_marks
            result.save()
            
            # Update RevaluationRequest model
            reval_request.revalued_marks = new_marks
            reval_request.marks_changed = marks_changed
            reval_request.status = 'COMPLETED'
            reval_request.admin_remarks = admin_remarks
            reval_request.processed_by = request.user
            reval_request.processed_at = timezone.now()
            reval_request.save()
            
            # Create notification for student
            from .signals import create_notification
            
            if marks_changed:
                message = (
                    f'Revaluation for {result.course.course_title} is completed. '
                    f'Your marks have been updated from {reval_request.original_marks} to {new_marks}.'
                )
            else:
                message = (
                    f'Revaluation for {result.course.course_title} is completed. '
                    f'Your marks remain {new_marks}.'
                )
            
            create_notification(
                student=result.student,
                notification_type='REVALUATION_COMPLETED',
                title='Revaluation Results Available',
                message=message,
                revaluation_request=reval_request
            )
            
            # Log the action
            from .signals import log_audit
            log_audit(
                action_type='REVALUATION_PROCESSED',
                student=result.student,
                user=request.user,
                description=f'Revaluation processed: {result.course.course_code} - Marks changed from {old_marks} to {new_marks}',
                metadata={
                    'result_id': result.id,
                    'course_code': result.course.course_code,
                    'original_marks': float(reval_request.original_marks),
                    'new_marks': float(new_marks),
                    'marks_changed': marks_changed
                }
            )
            
            messages.success(
                request, 
                f'Marks updated successfully! Changed from {old_marks} to {new_marks}. '
                f'Student has been notified.'
            )
            return redirect('admin:results_revaluationrequest_changelist')
            
        except ValueError:
            messages.error(request, 'Invalid marks value. Please enter a number.')
        except Exception as e:
            messages.error(request, f'Error updating marks: {str(e)}')
    
    context = {
        'result': result,
        'reval_request': reval_request,
        'student': result.student,
        'course': result.course,
    }
    
    return render(request, 'admin_panel/edit_revaluation.html', context)


# ============================================================================
# EDIT RESULT MARKS VIEW (For regular result editing)
# ============================================================================

@login_required
@user_passes_test(is_staff_or_professor)
def admin_edit_result(request, result_id):
    """
    Edit regular result marks (not revaluation).
    """
    result = get_object_or_404(Result, id=result_id)
    
    if request.method == 'POST':
        try:
            new_marks = float(request.POST.get('marks'))
            
            if new_marks < 0 or new_marks > 100:
                messages.error(request, 'Marks must be between 0 and 100.')
                return redirect('admin_edit_result', result_id=result_id)
            
            old_marks = result.final_cie_marks
            result.final_cie_marks = new_marks
            result.save()
            
            # Log the action
            from .signals import log_audit
            log_audit(
                action_type='RESULT_EDITED',
                student=result.student,
                user=request.user,
                description=f'Result edited: {result.course.course_code} - Marks changed from {old_marks} to {new_marks}',
                metadata={
                    'result_id': result.id,
                    'course_code': result.course.course_code,
                    'old_marks': float(old_marks),
                    'new_marks': float(new_marks)
                }
            )
            
            messages.success(request, f'Marks updated from {old_marks} to {new_marks}')
            return redirect('admin:results_result_changelist')
            
        except ValueError:
            messages.error(request, 'Invalid marks value.')
        except Exception as e:
            messages.error(request, f'Error: {str(e)}')
    
    context = {
        'result': result,
        'student': result.student,
        'course': result.course,
    }
    
    return render(request, 'admin_panel/edit_result.html', context)


# ============================================================================
# STUDENT RECEIPTS VIEW
# ============================================================================

@login_required
@user_passes_test(is_staff_or_professor)
def student_receipts(request, student_id):
    """
    View all receipts for a specific student.
    Shows both revaluation and makeup exam receipts.
    """
    student = get_object_or_404(Student, id=student_id)
    
    # Get all revaluation receipts
    revaluation_receipts = RevaluationRequest.objects.filter(
        student=student,
        receipt_url__isnull=False
    ).select_related('result__course').order_by('-created_at')
    
    # Get all makeup exam receipts
    makeup_receipts = MakeupExamRequest.objects.filter(
        student=student,
        receipt_url__isnull=False
    ).prefetch_related('subjects').order_by('-created_at')
    
    context = {
        'student': student,
        'revaluation_receipts': revaluation_receipts,
        'makeup_receipts': makeup_receipts,
        'total_receipts': revaluation_receipts.count() + makeup_receipts.count(),
    }
    
    return render(request, 'admin_panel/student_receipts.html', context)


# ============================================================================
# BULK DOWNLOAD RECEIPTS
# ============================================================================

@login_required
@user_passes_test(is_staff_or_professor)
def download_student_receipts(request, student_id):
    """
    Download all receipts for a student as a ZIP file.
    """
    import zipfile
    from io import BytesIO
    import os
    from django.conf import settings
    
    student = get_object_or_404(Student, id=student_id)
    
    # Create ZIP file in memory
    zip_buffer = BytesIO()
    
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        
        # Add revaluation receipts
        revaluation_receipts = RevaluationRequest.objects.filter(
            student=student,
            receipt_url__isnull=False
        )
        
        for receipt in revaluation_receipts:
            try:
                # Get file path from URL
                file_path = receipt.receipt_url.replace(settings.MEDIA_URL, '')
                full_path = os.path.join(settings.MEDIA_ROOT, file_path)
                
                if os.path.exists(full_path):
                    # Add to ZIP with organized folder structure
                    zip_path = f"revaluation/{os.path.basename(file_path)}"
                    zip_file.write(full_path, zip_path)
            except Exception as e:
                print(f"Error adding revaluation receipt: {e}")
        
        # Add makeup exam receipts
        makeup_receipts = MakeupExamRequest.objects.filter(
            student=student,
            receipt_url__isnull=False
        )
        
        for receipt in makeup_receipts:
            try:
                file_path = receipt.receipt_url.replace(settings.MEDIA_URL, '')
                full_path = os.path.join(settings.MEDIA_ROOT, file_path)
                
                if os.path.exists(full_path):
                    zip_path = f"makeup_exam/{os.path.basename(file_path)}"
                    zip_file.write(full_path, zip_path)
            except Exception as e:
                print(f"Error adding makeup receipt: {e}")
        
        # Add hall tickets
        hall_tickets = MakeupExamRequest.objects.filter(
            student=student,
            hall_ticket_url__isnull=False
        )
        
        for ticket in hall_tickets:
            try:
                file_path = ticket.hall_ticket_url.replace(settings.MEDIA_URL, '')
                full_path = os.path.join(settings.MEDIA_ROOT, file_path)
                
                if os.path.exists(full_path):
                    zip_path = f"hall_tickets/{os.path.basename(file_path)}"
                    zip_file.write(full_path, zip_path)
            except Exception as e:
                print(f"Error adding hall ticket: {e}")
    
    # Prepare response
    zip_buffer.seek(0)
    response = HttpResponse(zip_buffer.getvalue(), content_type='application/zip')
    response['Content-Disposition'] = f'attachment; filename="receipts_{student.usn}.zip"'
    
    return response



@login_required
@user_passes_test(is_staff_or_professor)
def student_search(request):
    """
    Advanced student search with filters and pagination.
    """
    query = request.GET.get('q', '')
    department = request.GET.get('department', '')
    has_failed = request.GET.get('has_failed', '')
    
    students = Student.objects.all()
    
    # Search filter
    if query:
        students = students.filter(
            Q(usn__icontains=query) |
            Q(name__icontains=query) |
            Q(department__icontains=query)
        )
    
    # Department filter
    if department:
        students = students.filter(department=department)
    
    # Batch filter
    
    # Failed students filter
    if has_failed == 'yes':
        failed_student_ids = Result.objects.filter(
            final_cie_marks__lt=40
        ).values_list('student_id', flat=True).distinct()
        students = students.filter(id__in=failed_student_ids)
    
    # Get filter options
    departments = Student.objects.values_list('department', flat=True).distinct().exclude(department__isnull=True)
    
    # Pagination
    paginator = Paginator(students.order_by('usn'), 50)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'students': page_obj,
        'query': query,
        'department': department,
        'has_failed': has_failed,
        'departments': departments,
        'total_count': students.count(),
    }
    
    return render(request, 'admin_panel/student_search.html', context)


@login_required
@user_passes_test(is_staff_or_professor)
def revaluation_management(request):
    """
    Manage all revaluation requests with search and filters.
    """
    query = request.GET.get('q', '')
    status_filter = request.GET.get('status', '')
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')
    
    requests_list = RevaluationRequest.objects.select_related(
        'student', 'result__course'
    ).all()
    
    # Search
    if query:
        requests_list = requests_list.filter(
            Q(student__usn__icontains=query) |
            Q(student__name__icontains=query) |
            Q(result__course__course_code__icontains=query) |
            Q(result__course__course_title__icontains=query)
        )
    
    # Status filter
    if status_filter:
        requests_list = requests_list.filter(status=status_filter)
    
    # Date filters
    if date_from:
        requests_list = requests_list.filter(created_at__gte=date_from)
    if date_to:
        requests_list = requests_list.filter(created_at__lte=date_to)
    
    # Statistics
    stats = {
        'total': RevaluationRequest.objects.count(),
        'pending': RevaluationRequest.objects.filter(status='PENDING').count(),
        'paid': RevaluationRequest.objects.filter(status='PAID').count(),
        'processing': RevaluationRequest.objects.filter(status='PROCESSING').count(),
        'completed': RevaluationRequest.objects.filter(status='COMPLETED').count(),
        'rejected': RevaluationRequest.objects.filter(status='REJECTED').count(),
    }
    
    # Pagination
    paginator = Paginator(requests_list.order_by('-created_at'), 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'requests': page_obj,
        'stats': stats,
        'query': query,
        'status_filter': status_filter,
        'date_from': date_from,
        'date_to': date_to,
        'total_count': requests_list.count(),
    }
    
    return render(request, 'admin_panel/revaluation_management.html', context)

@login_required
@user_passes_test(is_staff_or_professor)
def paperseeing_management(request):
    """
    Manage all paperseeing requests with search and filters.
    """
    query = request.GET.get('q', '')
    status_filter = request.GET.get('status', '')
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')
    
    requests_list = PaperSeeingRequest.objects.select_related(
        'student', 'result__course'
    ).all()
    
    # Search'
    if query:
        requests_list = requests_list.filter(
            Q(student__usn__icontains=query) |
            Q(student__name__icontains=query) |
            Q(result__course__course_code__icontains=query) |
            Q(result__course__course_title__icontains=query)
        )
    
    # Status filter
    if status_filter:
        requests_list = requests_list.filter(status=status_filter)
    
    # Date filters
    if date_from:
        requests_list = requests_list.filter(created_at__gte=date_from)
    if date_to:
        requests_list = requests_list.filter(created_at__lte=date_to)
    
    # Statistics
    stats = {
        'total': PaperSeeingRequest.objects.count(),
        'pending': PaperSeeingRequest.objects.filter(status='PENDING').count(),
        'paid': PaperSeeingRequest.objects.filter(status='PAID').count(),
        'processing': PaperSeeingRequest.objects.filter(status='PROCESSING').count(),
        'completed': PaperSeeingRequest.objects.filter(status='COMPLETED').count(),
        'rejected': PaperSeeingRequest.objects.filter(status='REJECTED').count(),
    }
    
    # Pagination
    paginator = Paginator(requests_list.order_by('-created_at'), 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'requests': page_obj,
        'stats': stats,
        'query': query,
        'status_filter': status_filter,
        'date_from': date_from,
        'date_to': date_to,
        'total_count': requests_list.count(),
    }
    
    return render(request, 'admin_panel/paperseeing_management.html', context)

@login_required
@user_passes_test(is_staff_or_professor)
def makeup_exam_management(request):
    """
    Manage all makeup exam requests with search and filters.
    """
    query = request.GET.get('q', '')
    status_filter = request.GET.get('status', '')
    verification_filter = request.GET.get('verification', '')
    
    requests_list = MakeupExamRequest.objects.select_related('student').prefetch_related('subjects').all()
    
    # Search
    if query:
        requests_list = requests_list.filter(
            Q(student__usn__icontains=query) |
            Q(student__name__icontains=query) |
            Q(exam_cycle__icontains=query)
        )
    
    # Status filter
    if status_filter:
        requests_list = requests_list.filter(status=status_filter)
    
    # Verification filter
    if verification_filter == 'pending_admin':
        requests_list = requests_list.filter(admin_verified=False)
    elif verification_filter == 'pending_proctor':
        requests_list = requests_list.filter(admin_verified=True, proctor_verified=False)
    elif verification_filter == 'approved':
        requests_list = requests_list.filter(admin_verified=True, proctor_verified=True)
    
    # Statistics
    stats = {
        'total': MakeupExamRequest.objects.count(),
        'paid': MakeupExamRequest.objects.filter(status='PAID').count(),
        'pending_admin': MakeupExamRequest.objects.filter(admin_verified=False).count(),
        'pending_proctor': MakeupExamRequest.objects.filter(
            admin_verified=True, proctor_verified=False
        ).count(),
        'approved': MakeupExamRequest.objects.filter(status='APPROVED').count(),
    }
    
    # Pagination
    paginator = Paginator(requests_list.order_by('-created_at'), 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'requests': page_obj,
        'stats': stats,
        'query': query,
        'status_filter': status_filter,
        'verification_filter': verification_filter,
        'total_count': requests_list.count(),
    }
    
    return render(request, 'admin_panel/makeup_exam_management.html', context)


@login_required
@user_passes_test(is_staff_or_professor)
def admin_verify_makeup_ajax(request, request_id):
    """
    Admin verification via AJAX (no page reload).
    """
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Invalid method'})
    
    try:
        makeup_request = get_object_or_404(MakeupExamRequest, id=request_id)
        action = request.POST.get('action')
        remarks = request.POST.get('remarks', '')
        
        if action == 'approve':
            makeup_request.admin_verified = True
            makeup_request.admin_verified_by = request.user
            makeup_request.admin_verified_at = timezone.now()
            makeup_request.admin_remarks = remarks
            makeup_request.status = 'ADMIN_VERIFIED'
            makeup_request.save()
            
            # Create notification
            from .signals import create_notification
            create_notification(
                student=makeup_request.student,
                notification_type='MAKEUP_ADMIN_VERIFIED',
                title='Makeup Exam: Admin Verified',
                message=f'Your makeup exam registration has been verified by admin. Awaiting proctor verification.',
                makeup_exam_request=makeup_request
            )
            
            return JsonResponse({
                'success': True,
                'message': 'Request approved successfully!'
            })
        
        elif action == 'reject':
            makeup_request.status = 'REJECTED'
            makeup_request.admin_remarks = remarks
            makeup_request.save()
            
            return JsonResponse({
                'success': True,
                'message': 'Request rejected.'
            })
        
        else:
            return JsonResponse({'success': False, 'error': 'Invalid action'})
    
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@login_required
@user_passes_test(lambda u: u.groups.filter(name='Proctor').exists() or u.is_superuser)
def proctor_verify_makeup_ajax(request, request_id):
    """
    Proctor verification via AJAX.
    """
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Invalid method'})
    
    try:
        makeup_request = get_object_or_404(MakeupExamRequest, id=request_id)
        
        if not makeup_request.admin_verified:
            return JsonResponse({
                'success': False,
                'error': 'Admin verification required first'
            })
        
        action = request.POST.get('action')
        remarks = request.POST.get('remarks', '')
        
        if action == 'approve':
            makeup_request.proctor_verified = True
            makeup_request.proctor_verified_by = request.user
            makeup_request.proctor_verified_at = timezone.now()
            makeup_request.proctor_remarks = remarks
            makeup_request.status = 'APPROVED'
            makeup_request.save()
            
            # Generate hall ticket
            from .services.receipt_service import generate_hall_ticket_file
            hall_ticket_url = generate_hall_ticket_file(makeup_request)
            makeup_request.hall_ticket_url = hall_ticket_url
            makeup_request.save()
            
            # Create notification
            from .signals import create_notification
            create_notification(
                student=makeup_request.student,
                notification_type='HALL_TICKET_READY',
                title='Hall Ticket Ready',
                message=f'Your makeup exam hall ticket is ready for download.',
                makeup_exam_request=makeup_request
            )
            
            return JsonResponse({
                'success': True,
                'message': 'Request approved! Hall ticket generated.'
            })
        
        elif action == 'reject':
            makeup_request.status = 'REJECTED'
            makeup_request.proctor_remarks = remarks
            makeup_request.save()
            
            return JsonResponse({
                'success': True,
                'message': 'Request rejected.'
            })
    
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@login_required
@user_passes_test(is_staff_or_professor)
def student_profile(request, student_id):
    """
    Complete student profile with all information and actions.
    """
    student = get_object_or_404(Student, id=student_id)
    
    try:
        metadata = student.metadata
    except StudentMetadata.DoesNotExist:
        metadata = None
    
    # Get all results
    results = Result.objects.filter(student=student).select_related('course').order_by('semester', 'course__course_code')
    
    # Get revaluation requests
    revaluation_requests = RevaluationRequest.objects.filter(student=student).select_related('result__course')
    
    # Get makeup exam requests
    makeup_requests = MakeupExamRequest.objects.filter(student=student).prefetch_related('subjects')
    
    # Get notifications
    notifications = StudentNotification.objects.filter(student=student).order_by('-created_at')[:10]
    
    # Statistics
    total_results = results.count()
    failed_count = results.filter(final_cie_marks__lt=40).count()
    avg_marks = results.aggregate(Avg('final_cie_marks'))['final_cie_marks__avg'] or 0
    
    context = {
        'student': student,
        'metadata': metadata,
        'results': results,
        'revaluation_requests': revaluation_requests,
        'makeup_requests': makeup_requests,
        'notifications': notifications,
        'total_results': total_results,
        'failed_count': failed_count,
        'avg_marks': round(avg_marks, 2),
    }
    
    return render(request, 'admin_panel/student_profile.html', context)
