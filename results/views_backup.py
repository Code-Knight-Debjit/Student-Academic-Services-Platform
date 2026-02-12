"""
Views for Student Results System.
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.http import HttpResponse, JsonResponse
from django.db.models import Q, Avg, Count
from django_ratelimit.decorators import ratelimit
from datetime import datetime
import os

from student_results import settings

from .models import Student, StudentMetadata, Course, Result, UploadHistory
from .forms import ResultQueryForm, BulkUploadForm, ResultEditForm
from .utils import process_results_excel, process_metadata_excel
from .pdf_generator import generate_result_pdf
from django.conf import settings  # If not already imported
from decimal import Decimal
from .models import (
        RevaluationConfiguration,
        RevaluationRequest,
        MakeupExamConfiguration,
        MakeupExamRequest
    )

def is_staff_or_professor(user):
    """Check if user is staff or superuser."""
    return user.is_staff or user.is_superuser


@ratelimit(key='ip', rate='10/m', method='POST')
@ratelimit(key='ip', rate='10/m', method='POST')
def home(request):
    """Home page with result query form - ENHANCED VERSION."""
    context = {
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
            if settings.RECAPTCHA_SECRET_KEY:  # Only verify if configured
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
                except:
                    reval_config = None
                
                # ===== NEW: Check revaluation status for each result =====
                results_with_reval = []
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
                    
                    results_with_reval.append({
                        'result': result,
                        'can_request_reval': can_request_reval,
                        'reval_status': existing_reval.status if existing_reval else None,
                        'reval_request': existing_reval
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
                    'results_with_reval': results_with_reval,  # NEW: Enhanced results
                    'semester': semester,
                    'total_marks': total_marks,
                    'avg_marks': round(avg_marks, 2),
                    'show_results': True,
                    
                    # NEW: Revaluation feature
                    'reval_config': reval_config,
                    
                    # NEW: Makeup exam feature
                    'show_makeup_tab': show_makeup_tab,
                    'failed_count': failed_count,
                }
                
                # ===== Use enhanced template (or keep existing) =====
                # Option 1: Use new template with tabs
                # return render(request, 'results/result_view_extended.html', context)
                
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
def admin_panel(request):
    """Admin dashboard with analytics."""
    total_students = Student.objects.count()
    total_results = Result.objects.count()
    total_courses = Course.objects.count()
    try:
        revaluation_count = RevaluationRequest.objects.count()
        pending_revaluation = RevaluationRequest.objects.filter(status='PAID').count()
        makeup_exam_count = MakeupExamRequest.objects.count()
        pending_makeup = MakeupExamRequest.objects.filter(
            status='PAID', admin_verified=False
        ).count()
    except:
        revaluation_count = 0
        pending_revaluation = 0
        makeup_exam_count = 0
        pending_makeup = 0
    # Recent uploads
    recent_uploads = UploadHistory.objects.all()[:10]
    
    # Semester-wise statistics
    semester_stats = Result.objects.values('semester').annotate(
        count=Count('id'),
        avg_marks=Avg('final_cie_marks')
    ).order_by('semester')
    
    # Admission route statistics
    route_stats = StudentMetadata.objects.values('admission_route').annotate(
        count=Count('student')
    ).order_by('-count')
    
    context = {
        'total_students': total_students,
        'total_results': total_results,
        'total_courses': total_courses,
        'recent_uploads': recent_uploads,
        'semester_stats': semester_stats,
        'route_stats': route_stats,
        'revaluation_count': revaluation_count,
        'pending_revaluation': pending_revaluation,
        'makeup_exam_count': makeup_exam_count,
        'pending_makeup': pending_makeup,
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

@ratelimit(key='ip', rate='10/m', method='POST')
def create_revaluation_order(request):
    """Create Razorpay order for revaluation."""
    from .services.payment_service import RevaluationPaymentService
    
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
            return JsonResponse({
                'success': True,
                'order_id': order_response['order_id'],
                'amount': float(order_response['amount']),
                'currency': 'INR',
                'razorpay_key': settings.RAZORPAY_KEY_ID,
                'student_name': student.name,
            })
        else:
            return JsonResponse(order_response, status=400)
    
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@ratelimit(key='ip', rate='10/m', method='POST')
def verify_revaluation_payment(request):
    """Verify and complete revaluation payment."""
    from .services.payment_service import RevaluationPaymentService
    
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
                'receipt_url': result.get('receipt_url', '')
            })
        else:
            return JsonResponse(result, status=400)
    
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


# Makeup Exam Views
# -----------------

@ratelimit(key='ip', rate='20/m', method='GET')
def makeup_exam_page(request, usn, semester):
    """Display makeup exam registration page for failed subjects."""
    try:
        student = get_object_or_404(Student, usn=usn)
        
        # Get failed subjects
        failed_results = get_failed_subjects(student, semester)
        
        if not failed_results.exists():
            messages.info(request, 'You have no failed subjects.')
            return redirect('home')
        
        # Get configuration
        try:
            config = MakeupExamConfiguration.objects.first()
        except:
            config = None
        
        # Check for existing request
        existing_request = None
        try:
            existing_request = MakeupExamRequest.objects.filter(
                student=student,
                semester=semester,
                status__in=['PENDING', 'PAID', 'ADMIN_VERIFIED', 'PROCTOR_VERIFIED', 'APPROVED']
            ).first()
        except:
            pass
        
        context = {
            'student': student,
            'semester': semester,
            'failed_results': failed_results,
            'config': config,
            'existing_request': existing_request,
            'can_register': config and config.is_active() and not existing_request,
        }
        
        return render(request, 'results/makeup_exam.html', context)
        
    except Exception as e:
        messages.error(request, f'Error: {str(e)}')
        return redirect('home')


@ratelimit(key='ip', rate='10/m', method='POST')
def create_makeup_exam_order(request):
    """Create Razorpay order for makeup exam registration."""
    from .services.payment_service import MakeupExamPaymentService
    
    try:
        usn = request.POST.get('usn')
        semester = int(request.POST.get('semester'))
        subject_ids = request.POST.getlist('subjects[]')
        
        student = get_object_or_404(Student, usn=usn)
        subjects = Course.objects.filter(id__in=subject_ids)
        
        if not subjects.exists():
            return JsonResponse({
                'success': False,
                'error': 'No subjects selected'
            }, status=400)
        
        # Get configuration
        config = MakeupExamConfiguration.objects.first()
        if not config or not config.is_active():
            return JsonResponse({
                'success': False,
                'error': 'Makeup exam registration is currently closed'
            })
        
        # Validate subjects are actually failed
        failed_subject_ids = get_failed_subjects(student, semester).values_list('course_id', flat=True)
        invalid_subjects = [s.id for s in subjects if s.id not in failed_subject_ids]
        
        if invalid_subjects:
            return JsonResponse({
                'success': False,
                'error': 'You can only register for failed subjects'
            }, status=400)
        
        # Create payment order
        payment_service = MakeupExamPaymentService()
        order_response = payment_service.create_makeup_exam_order(
            student=student,
            subjects=list(subjects),
            semester=semester,
            config=config
        )
        
        if order_response['success']:
            return JsonResponse({
                'success': True,
                'order_id': order_response['order_id'],
                'amount': float(order_response['amount']),
                'currency': 'INR',
                'razorpay_key': settings.RAZORPAY_KEY_ID,
                'student_name': student.name,
                'subject_count': order_response['subject_count']
            })
        else:
            return JsonResponse(order_response, status=400)
    
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@ratelimit(key='ip', rate='10/m', method='POST')
def verify_makeup_exam_payment(request):
    """Verify and complete makeup exam payment."""
    from .services.payment_service import MakeupExamPaymentService
    
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
        payment_service = MakeupExamPaymentService()
        result = payment_service.complete_payment(order_id, payment_id, signature)
        
        if result['success']:
            return JsonResponse({
                'success': True,
                'message': 'Payment successful! Your makeup exam registration has been submitted for verification.',
                'receipt_url': result.get('receipt_url', '')
            })
        else:
            return JsonResponse(result, status=400)
    
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


# Hall Ticket Generation
# ----------------------

@ratelimit(key='ip', rate='10/m', method='GET')
def download_hall_ticket(request, request_id):
    """Generate and download makeup exam hall ticket."""
    from .services.hall_ticket_service import generate_hall_ticket_pdf
    
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
