"""
Context processor for notification counts in navigation.

LOCATION: results/context_processors.py

This adds badge counts to the navigation menu automatically.
"""

from results.models import (
    RevaluationRequest, 
    MakeupExamRequest,
    StudentNotification
)


def notification_counts(request):
    """
    Add notification counts to template context.
    
    This makes badge counts available in all templates,
    especially useful for navigation menus.
    
    Returns:
        dict: Notification counts for various user roles
    """
    counts = {
        'pending_revaluation_count': 0,
        'pending_makeup_count': 0,
        'pending_proctor_count': 0,
        'student_unread_count': 0,
    }
    
    if not request.user.is_authenticated:
        return counts
    
    # Admin/Staff counts
    if request.user.is_staff or request.user.is_superuser:
        # Revaluation requests awaiting admin action
        counts['pending_revaluation_count'] = RevaluationRequest.objects.filter(
            status='PAID'
        ).count()
        
        # Makeup exam requests awaiting admin verification
        counts['pending_makeup_count'] = MakeupExamRequest.objects.filter(
            status='PAID',
            admin_verified=False
        ).count()
    
    # Proctor counts
    if request.user.groups.filter(name='Proctor').exists() or request.user.is_superuser:
        # Requests awaiting proctor verification (admin already verified)
        counts['pending_proctor_count'] = MakeupExamRequest.objects.filter(
            admin_verified=True,
            proctor_verified=False
        ).count()
    
    # Student counts (if students can log in)
    # This is for future enhancement if you add student login
    try:
        from results.models import Student
        student = Student.objects.filter(
            # Add your student-user relationship here
            # Example: user=request.user
        ).first()
        
        if student:
            counts['student_unread_count'] = StudentNotification.objects.filter(
                student=student,
                is_read=False
            ).count()
    except:
        pass
    
    return counts


def exam_configurations(request):
    """
    Add exam configuration status to template context.
    
    Makes it easy to show/hide features based on windows being open.
    
    Returns:
        dict: Configuration status flags
    """
    from results.models import (
        RevaluationConfiguration,
        MakeupExamConfiguration
    )
    
    config_status = {
        'revaluation_window_open': False,
        'makeup_exam_registration_open': False,
        'revaluation_config': None,
        'makeup_exam_config': None,
    }
    
    try:
        reval_config = RevaluationConfiguration.objects.first()
        if reval_config:
            config_status['revaluation_window_open'] = reval_config.is_active()
            config_status['revaluation_config'] = reval_config
    except:
        pass
    
    try:
        makeup_config = MakeupExamConfiguration.objects.first()
        if makeup_config:
            config_status['makeup_exam_registration_open'] = makeup_config.is_active()
            config_status['makeup_exam_config'] = makeup_config
    except:
        pass
    
    return config_status


def user_permissions(request):
    """
    Add user permission flags to template context.
    
    Makes it easier to show/hide UI elements based on permissions.
    
    Returns:
        dict: Permission flags
    """
    permissions = {
        'is_admin': False,
        'is_proctor': False,
        'can_verify_revaluation': False,
        'can_verify_makeup_exam': False,
    }
    
    if not request.user.is_authenticated:
        return permissions
    
    # Check admin status
    if request.user.is_staff or request.user.is_superuser:
        permissions['is_admin'] = True
        permissions['can_verify_revaluation'] = True
        permissions['can_verify_makeup_exam'] = True
    
    # Check proctor status
    if request.user.groups.filter(name='Proctor').exists():
        permissions['is_proctor'] = True
        permissions['can_verify_makeup_exam'] = True
    
    return permissions


# ============================================================================
# USAGE IN settings.py:
# ============================================================================
# 
# TEMPLATES = [
#     {
#         'BACKEND': 'django.template.backends.django.DjangoTemplates',
#         'DIRS': [BASE_DIR / 'templates'],
#         'APP_DIRS': True,
#         'OPTIONS': {
#             'context_processors': [
#                 'django.template.context_processors.debug',
#                 'django.template.context_processors.request',
#                 'django.contrib.auth.context_processors.auth',
#                 'django.contrib.messages.context_processors.messages',
#                 
#                 # ADD THESE:
#                 'results.context_processors.notification_counts',
#                 'results.context_processors.exam_configurations',
#                 'results.context_processors.user_permissions',
#             ],
#         },
#     },
# ]
#
# ============================================================================


# ============================================================================
# USAGE IN TEMPLATES:
# ============================================================================
#
# {% if pending_revaluation_count > 0 %}
#     <span class="badge">{{ pending_revaluation_count }}</span>
# {% endif %}
#
# {% if revaluation_window_open %}
#     <button>Request Revaluation</button>
# {% endif %}
#
# {% if is_admin %}
#     <a href="{% url 'admin_panel' %}">Admin Dashboard</a>
# {% endif %}
#
# {% if is_proctor %}
#     <a href="{% url 'proctor_makeup_exam_requests' %}">
#         Verify Requests
#         {% if pending_proctor_count > 0 %}
#             <span>{{ pending_proctor_count }}</span>
#         {% endif %}
#     </a>
# {% endif %}
#
# ============================================================================