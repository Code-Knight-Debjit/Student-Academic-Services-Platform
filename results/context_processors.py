"""
Context processor for notification counts in navigation.

LOCATION: results/context_processors.py

This adds badge counts to the navigation menu automatically.
"""
from django.core.cache import cache
from results.models import (
    RevaluationRequest, 
    MakeupExamRequest,
    RevaluationConfiguration,
    MakeupExamConfiguration
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
    # ✅ Only query DB if user is actually logged in as staff
    if not request.user.is_authenticated:
        return counts  # ← returns immediately for all public users — ZERO DB queries
    
    if request.user.is_staff or request.user.is_superuser:
        cache_key = 'nav_counts_admin'
        cached = cache.get(cache_key)
        if cached:
            return cached
        counts['pending_revaluation_count'] = RevaluationRequest.objects.filter(status='PAID').count()
        counts['pending_makeup_count'] = MakeupExamRequest.objects.filter(status='PAID', admin_verified=False).count()
        cache.set(cache_key, counts, 60)  # cache for 60s
    return counts


def exam_configurations(request):
    """
    Add exam configuration status to template context.
    
    Makes it easy to show/hide features based on windows being open.
    
    Returns:
        dict: Configuration status flags
    """
    cache_key = 'exam_config_status'
    cached = cache.get(cache_key)
    if cached:
        return cached
    
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

    cache.set(cache_key, config_status, 300)
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

if __name__ == "__main__":
    print("This is a Django context processor module. It should not be run directly.")