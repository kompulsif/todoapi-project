from kombu import Exchange, Queue
from datetime import timedelta
from config import REDIS_ADDR, REDIS_PORT, redis_db

broker_url = f"redis://{REDIS_ADDR}:{REDIS_PORT}/{redis_db}"
result_backend = f"redis://{REDIS_ADDR}:{REDIS_PORT}/{redis_db}"

worker_max_tasks_per_child = 10
worker_max_memory_per_child = 100000
task_acks_late = True
worker_prefetch_multiplier = 1
broker_heartbeat = 30
broker_connection_retry_on_startup = True
worker_log_format = "[%(asctime)s: %(levelname)s/%(processName)s] %(message)s"
worker_task_log_format = "[%(asctime)s: %(levelname)s/%(processName)s] [%(task_name)s(%(task_id)s)] %(message)s"
task_default_queue = "default-queue"

task_queues = [
    Queue(
        "default-queue", Exchange("default-queue"), routing_key="default-queue", queue_arguments={"x-max-priority": 7}
    ),
    Queue(
        "email-actions", Exchange("email-actions"), routing_key="email-actions", queue_arguments={"x-max-priority": 10}
    ),
]

task_routes = {
    "apps.celery_app.tasks.email.tasks.*": {
        "queue": "email-actions",
        "routing_key": "email-actions",
    },
}

beat_schedule = {
    "user_task_check_beat": {
        "task": "apps.celery_app.tasks.email.tasks.check_end_dates",
        "schedule": timedelta(hours=12),
        "options": {"priority": 5},
    }
}
