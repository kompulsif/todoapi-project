from apps.models.exceptions.celery import RetryTaskException
from pathlib import Path

TASK_MAX_RETRIES = 3
TASK_RETRY_COUNTDOWN = 5

task_retry_kwargs = {
    "bind": True,
    "autoretry_for": (RetryTaskException,),
    "retry_kwargs": {
        "max_retries": TASK_MAX_RETRIES,
    },
    "retry_backoff": TASK_RETRY_COUNTDOWN,
    "retry_jitter": True,
}
TEMPLATES_DIR = Path(__file__).resolve().parent / "mail_templates"
