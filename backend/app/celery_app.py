import os
from celery import Celery

redis_url = os.environ.get("REDIS_URL", "redis://redis:6379/0")

celery = Celery(
    "streamsculptor",
    broker=redis_url,
    backend=redis_url,
    include=["app.tasks.process_vod"],  # 👈 importa las tareas
)

celery.conf.task_routes = {
    "app.tasks.process_vod.*": {"queue": "vod"},
}
