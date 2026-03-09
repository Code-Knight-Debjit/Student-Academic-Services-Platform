"""
results/management/commands/cache_info.py
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Inspect or clear Redis cache keys from the command line.

Usage
-----
    python manage.py cache_info                  # list all sasp:* keys + sizes
    python manage.py cache_info --clear          # flush ALL sasp:* keys
    python manage.py cache_info --clear-analytics # flush analytics keys only
"""

from django.core.management.base import BaseCommand
from django.core.cache import cache
from results.cache import invalidate_all, invalidate_analytics


class Command(BaseCommand):
    help = "Inspect or clear Redis cache keys for the SASP application."

    def add_arguments(self, parser):
        parser.add_argument("--clear",            action="store_true", help="Flush ALL sasp:* keys.")
        parser.add_argument("--clear-analytics",  action="store_true", help="Flush analytics keys only.")

    def handle(self, *args, **options):
        if options["clear"]:
            invalidate_all()
            self.stdout.write(self.style.SUCCESS("All sasp:* cache keys cleared."))
            return

        if options["clear_analytics"]:
            invalidate_analytics()
            self.stdout.write(self.style.SUCCESS("Analytics cache keys cleared."))
            return

        # ── List mode ───────────────────────────────────────────────────────
        if not hasattr(cache, "delete_pattern"):
            self.stdout.write(self.style.WARNING(
                "Cache backend does not support key listing (not django-redis). "
                "Switch to django-redis in production to use this command."
            ))
            return

        client = cache.client.get_client()
        keys   = client.keys("sasp:*")

        if not keys:
            self.stdout.write("No sasp:* keys found in Redis.")
            return

        self.stdout.write(f"{'KEY':<60} {'TTL (s)':>8}  {'SIZE (bytes)':>12}")
        self.stdout.write("-" * 85)

        total_bytes = 0
        for raw_key in sorted(keys):
            key = raw_key.decode() if isinstance(raw_key, bytes) else raw_key
            ttl   = client.ttl(raw_key)
            try:
                size = client.memory_usage(raw_key) or 0
            except Exception:
                size = 0
            total_bytes += size
            self.stdout.write(f"{key:<60} {ttl:>8}  {size:>12,}")

        self.stdout.write("-" * 85)
        self.stdout.write(f"Total: {len(keys)} keys  |  {total_bytes:,} bytes  ({total_bytes/1024:.1f} KB)")