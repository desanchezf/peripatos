import os
from celery import Celery

# Configurar Django settings
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "project.settings")

# Crear instancia de Celery
app = Celery("project")

# Configurar Celery usando Django settings
app.config_from_object("django.conf:settings", namespace="CELERY")

# Auto-descubrir tareas en todas las apps de Django
app.autodiscover_tasks()

# Configuración adicional
app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Europe/Madrid",
    enable_utc=True,
)


@app.task(bind=True)
def debug_task(self):
    print(f"Request: {self.request!r}")
