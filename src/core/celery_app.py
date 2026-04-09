import logging
from celery import Celery
from src.core.config import settings
from src.core.logging import setup_logging

setup_logging()
logger = logging.getLogger(__name__)

celery_app = Celery(
    "sovereign_tasks",
    broker=f"redis://{settings.REDIS_HOST}:{settings.REDIS_PORT}/0",
    backend=f"redis://{settings.REDIS_HOST}:{settings.REDIS_PORT}/0",
    include=["src.tasks.ingestion_tasks"]
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
)

logger.info(
    "Configured Celery broker for redis://%s:%s/0",
    settings.REDIS_HOST,
    settings.REDIS_PORT,
)
