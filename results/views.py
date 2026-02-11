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

from .models import Student, StudentMetadata, Course, Result, UploadHistory
from .forms import ResultQueryForm, BulkUploadForm, ResultEditForm
from .utils import process_results_excel, process_metadata_excel
from .pdf_generator import generate_result_pdf


def is_staff_or_professor(user):
    """Check if user is staff or superuser."""
    return user.is_staff or user.is_superuser


@ratelimit(key='ip', rate='10/m', method='POST')
def home(request):
    """Home page with result query form."""
    context = {
        'form': ResultQueryForm(),
        'show_skeleton': False,
        'error_message': None,
        'results': None
    }
    
    if request.method == 'POST':
        form = ResultQueryForm(request.POST)
        
        if form.is_valid():
            # Verify reCAPTCHA
            recaptcha_response = request.POST.get('g-recaptcha-response', '')
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
                
                # Calculate statistics
                total_marks = sum([r.final_cie_marks for r in results if r.final_cie_marks])
                avg_marks = total_marks / results.count() if results.count() > 0 else 0
                
                context['student'] = student
                context['metadata'] = metadata
                context['results'] = results
                context['semester'] = semester
                context['total_marks'] = total_marks
                context['avg_marks'] = round(avg_marks, 2)
                context['show_results'] = True
                
                return render(request, 'results/result_view.html', context)
                
            except Student.DoesNotExist:
                context['error_message'] = 'Invalid USN'
                context['form'] = form
                return render(request, 'results/home.html', context)
        else:
            context['form'] = form
            context['error_message'] = 'Please correct the errors below'
    
    return render(request, 'results/home.html', context)


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

