"""
results/management/commands/warm_cache.py
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Django management command that pre-populates Redis before traffic hits.

Usage
-----
    python manage.py warm_cache                  # warm all students
    python manage.py warm_cache --semester 3     # only semester 3
    python manage.py warm_cache --usn 1JS21CS001 # single student

When to run
-----------
- After a fresh deploy (add to your entrypoint or docker-compose command)
- After a large bulk upload to prime the cache proactively
- In a cron job on a schedule

Why it matters
--------------
On a cold start every student's first request hits the database.  Running
warm_cache converts those cold misses into cache hits so the first real
user gets a fast response.
"""

import logging
from django.core.management.base import BaseCommand
from django.db.models import Prefetch

from results.models import Student, StudentMetadata, Result, RevaluationConfiguration, PaperSeeingConfiguration, RevaluationRequest, PaperSeeingRequest
from results.cache import set_cached_student_result
from results.views import (
    _build_cache_payload,
    _serialise_result_row,
    _serialise_reval_request,
    _serialise_paperseeing_request,
)
logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Pre-populate the Redis cache with student result data."

    def add_arguments(self, parser):
        parser.add_argument(
            "--semester", type=int, default=None,
            help="Only warm results for this semester number."
        )
        parser.add_argument(
            "--usn", type=str, default=None,
            help="Only warm results for this single USN."
        )

    def handle(self, *args, **options):
        semester_filter = options["semester"]
        usn_filter      = options["usn"]

        self.stdout.write(self.style.NOTICE("Starting cache warm-up …"))

        students = Student.objects.select_related("metadata")
        if usn_filter:
            students = students.filter(usn=usn_filter.upper())

        warmed  = 0
        skipped = 0

        for student in students.iterator(chunk_size=200):
            try:
                metadata = student.metadata
            except StudentMetadata.DoesNotExist:
                skipped += 1
                continue

            # Determine which semesters to warm for this student
            semesters = [semester_filter] if semester_filter else range(1, 9)

            for sem in semesters:
                results_qs = (
                    Result.objects
                    .filter(student=student, semester=sem)
                    .select_related("course")
                    .order_by("course__course_code")
                )
                if not results_qs.exists():
                    continue

                reval_config       = RevaluationConfiguration.objects.first()
                paperseeing_config = PaperSeeingConfiguration.objects.first()
                result_ids         = list(results_qs.values_list("pk", flat=True))

                reval_map = {
                    r.result_id: r for r in
                    RevaluationRequest.objects.filter(student=student, result_id__in=result_ids)
                }
                paperseeing_map = {
                    r.result_id: r for r in
                    PaperSeeingRequest.objects.filter(student=student, result_id__in=result_ids)
                }

                reval_open       = bool(reval_config and reval_config.is_active())
                paperseeing_open = bool(paperseeing_config and paperseeing_config.is_active())

                results_with_state = [
                    _serialise_result_row(
                        result=r,
                        reval_req=_serialise_reval_request(reval_map.get(r.pk)),
                        can_reval=reval_open and r.pk not in reval_map,
                        paperseeing_req=_serialise_paperseeing_request(paperseeing_map.get(r.pk)),
                        can_paperseeing=paperseeing_open and r.pk not in paperseeing_map,
                    )
                    for r in results_qs
                ]

                data = _build_cache_payload(
                    student=student, metadata=metadata, results_qs=results_qs,
                    reval_config=reval_config, paperseeing_config=paperseeing_config,
                    results_with_state=results_with_state,
                )
                set_cached_student_result(student.usn, sem, data)
                warmed += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Cache warm-up complete. Warmed: {warmed} entries, Skipped: {skipped} students."
            )
        )