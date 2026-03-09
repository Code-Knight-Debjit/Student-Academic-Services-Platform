"""
results/cache.py
~~~~~~~~~~~~~~~~
Central Redis caching layer for the Student Academic Services Platform.

This module provides:
  - A low-level cache_get / cache_set / cache_delete / cache_invalidate_pattern API
  - High-level helpers used directly from views (get_student_result, get_analytics, …)
  - A signal-wired invalidation strategy so the cache is automatically cleared
    whenever a Result or Student record changes in the database.

All cache keys follow the convention:
    sasp:<entity>:<discriminator>
e.g. sasp:result:1JS21CS001:3
     sasp:analytics:semester:3
     sasp:analytics:dashboard

TTL constants are defined in one place so they are easy to tune.
"""

import json
import logging
from functools import wraps
from django.core.cache import cache

logger = logging.getLogger(__name__)
def make_key(key: str, key_prefix: str, version: int) -> str:
    """
    Custom key function for django-redis.

    Django's default key constructor produces  :<version>:<prefix>:<key>
    which means our  sasp:result:USN:1  becomes  :1::sasp:result:USN:1
    in Redis, breaking cache_info pattern scans and direct redis-cli inspection.

    This function returns the key exactly as-is so what we write in code
    is what appears in Redis — bare  sasp:result:USN:1  with no mangling.
    """
    return key
# ---------------------------------------------------------------------------
# TTL constants (seconds)
# ---------------------------------------------------------------------------
TTL_RESULT        = 60 * 30          # 30 min  — student result pages
TTL_ANALYTICS     = 60 * 60          # 1 hour  — analytics / dashboard
TTL_TOP_PERFORMERS = 60 * 60 * 2    # 2 hours — top-performer lists
TTL_COURSE_STATS  = 60 * 60 * 2     # 2 hours — per-course statistics
TTL_UPLOAD_HISTORY = 60 * 15        # 15 min  — upload history log


# ---------------------------------------------------------------------------
# Key builders
# Keep all key construction in one place to prevent typos across the codebase.
# ---------------------------------------------------------------------------

def _result_key(usn: str, semester: int) -> str:
    """Cache key for a single student's result card."""
    return f"sasp:result:{usn.upper()}:{semester}"


def _analytics_dashboard_key() -> str:
    """Cache key for the overall admin dashboard statistics."""
    return "sasp:analytics:dashboard"


def _analytics_semester_key(semester: int) -> str:
    """Cache key for semester-specific analytics."""
    return f"sasp:analytics:semester:{semester}"


def _top_performers_key(semester: int, limit: int = 10) -> str:
    return f"sasp:top_performers:{semester}:{limit}"


def _course_stats_key(course_code: str) -> str:
    return f"sasp:course_stats:{course_code}"


def _upload_history_key() -> str:
    return "sasp:upload_history"


# ---------------------------------------------------------------------------
# Low-level helpers
# ---------------------------------------------------------------------------

def cache_get(key: str):
    """
    Retrieve a value from Redis.

    Returns the deserialised Python object on a cache hit, or None on a miss.
    Errors are caught and logged so a Redis outage never crashes the site.
    """
    try:
        value = cache.get(key)
        if value is not None:
            logger.debug("Cache HIT  → %s", key)
        else:
            logger.debug("Cache MISS → %s", key)
        return value
    except Exception as exc:
        logger.error("cache_get error for key '%s': %s", key, exc)
        return None


def cache_set(key: str, value, timeout: int):
    """
    Store a value in Redis with the given TTL (seconds).

    Django's cache framework serialises the value with pickle by default,
    so any picklable Python object (dict, list, QuerySet result, …) is fine.
    """
    try:
        cache.set(key, value, timeout=timeout)
        logger.debug("Cache SET  → %s (ttl=%ds)", key, timeout)
    except Exception as exc:
        logger.error("cache_set error for key '%s': %s", key, exc)


def cache_delete(key: str):
    """Remove a single key from Redis."""
    try:
        cache.delete(key)
        logger.debug("Cache DEL  → %s", key)
    except Exception as exc:
        logger.error("cache_delete error for key '%s': %s", key, exc)


def cache_invalidate_pattern(pattern: str):
    """
    Delete all keys matching a glob-style pattern, e.g. 'sasp:analytics:*'.

    Uses cache.delete_pattern() which is provided by django-redis.
    Falls back gracefully if the method is unavailable (e.g. LocMemCache in tests).
    """
    try:
        if hasattr(cache, "delete_pattern"):
            deleted = cache.delete_pattern(pattern)
            logger.info("Cache PURGE pattern '%s' → %s key(s) removed", pattern, deleted)
        else:
            # Test environments use LocMemCache which has no delete_pattern.
            logger.warning(
                "cache.delete_pattern not available; skipping invalidation of '%s'", pattern
            )
    except Exception as exc:
        logger.error("cache_invalidate_pattern error for '%s': %s", pattern, exc)


# ---------------------------------------------------------------------------
# High-level result helpers
# ---------------------------------------------------------------------------

def get_cached_student_result(usn: str, semester: int):
    """Return cached result data for (usn, semester), or None on miss."""
    return cache_get(_result_key(usn, semester))


def set_cached_student_result(usn: str, semester: int, data: dict):
    """
    Cache serialisable result data for a student.

    `data` should be a plain dict (not a QuerySet) so it survives
    pickle round-trips without pulling in database connections.
    """
    cache_set(_result_key(usn, semester), data, TTL_RESULT)


def invalidate_student_result(usn: str, semester: int):
    """Remove cached result for a specific student + semester."""
    cache_delete(_result_key(usn, semester))


def invalidate_all_results_for_student(usn: str):
    """
    Purge all semester results for a student (used when student metadata changes).
    """
    cache_invalidate_pattern(f"sasp:result:{usn.upper()}:*")


# ---------------------------------------------------------------------------
# High-level analytics helpers
# ---------------------------------------------------------------------------

def get_cached_dashboard():
    return cache_get(_analytics_dashboard_key())


def set_cached_dashboard(data: dict):
    cache_set(_analytics_dashboard_key(), data, TTL_ANALYTICS)


def get_cached_semester_analytics(semester: int):
    return cache_get(_analytics_semester_key(semester))


def set_cached_semester_analytics(semester: int, data: dict):
    cache_set(_analytics_semester_key(semester), data, TTL_ANALYTICS)


def get_cached_top_performers(semester: int, limit: int = 10):
    return cache_get(_top_performers_key(semester, limit))


def set_cached_top_performers(semester: int, data: list, limit: int = 10):
    cache_set(_top_performers_key(semester, limit), data, TTL_TOP_PERFORMERS)


def get_cached_course_stats(course_code: str):
    return cache_get(_course_stats_key(course_code))


def set_cached_course_stats(course_code: str, data: dict):
    cache_set(_course_stats_key(course_code), data, TTL_COURSE_STATS)


def get_cached_upload_history():
    return cache_get(_upload_history_key())


def set_cached_upload_history(data: list):
    cache_set(_upload_history_key(), data, TTL_UPLOAD_HISTORY)


def invalidate_analytics():
    """
    Wipe all analytics-related keys.
    Called after any bulk upload or result edit so the next request
    recomputes fresh aggregates from the database.
    """
    cache_invalidate_pattern("sasp:analytics:*")
    cache_invalidate_pattern("sasp:top_performers:*")
    cache_invalidate_pattern("sasp:course_stats:*")
    cache_delete(_upload_history_key())
    logger.info("All analytics cache keys invalidated.")


def invalidate_all():
    """Nuclear option: flush every SASP key. Use with care."""
    cache_invalidate_pattern("sasp:*")
    logger.warning("ALL cache keys invalidated (sasp:*).")