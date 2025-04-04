from celery import Celery

app = Celery()
app.config_from_object("apps.celery_app.celery_config")
app.autodiscover_tasks(["apps.celery_app.tasks.email.tasks.*"])
