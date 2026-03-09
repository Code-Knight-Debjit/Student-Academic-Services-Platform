"""
results/apps.py
~~~~~~~~~~~~~~~
AppConfig for the `results` application.

The ready() hook is the correct place to import signals because Django
guarantees that all models are loaded before ready() is called.
Importing signals at module level (e.g. top of models.py) can cause
AppRegistryNotReady errors in some Django start-up orders.
"""

from django.apps import AppConfig


class ResultsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "results"

    def ready(self):
        # Importing the signals module here registers all @receiver decorators.
        import results.signals  # noqa: F401