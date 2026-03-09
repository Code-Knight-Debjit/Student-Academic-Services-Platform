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

from results.models import Student, StudentMetadata, Result
from results.cache import set_cached_student_result
from results.views import _serialise_result   # reuse the serialiser

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

        students = Student.objects.select_related("studentmetadata")
        if usn_filter:
            students = students.filter(usn=usn_filter.upper())

        warmed  = 0
        skipped = 0

        for student in students.iterator(chunk_size=200):
            try:
                metadata = student.studentmetadata
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

                data = _serialise_result(student, metadata, results_qs)
                set_cached_student_result(student.usn, sem, data)
                warmed += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Cache warm-up complete. Warmed: {warmed} entries, Skipped: {skipped} students."
            )
        )