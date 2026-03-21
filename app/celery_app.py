from celery import Celery
from .config import settings

celery_app = Celery(
    "rootnode",
    broker=settings.broker_url,
    backend=settings.result_backend,
    include=["app.tasks"]
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
)
