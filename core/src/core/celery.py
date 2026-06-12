import os
from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')

app = Celery('core')

# Charge toute config préfixée CELERY_* depuis settings.py
app.config_from_object('django.conf:settings', namespace='CELERY')

# Découvre automatiquement les tasks.py dans chaque app INSTALLED_APPS
app.autodiscover_tasks()

# Forcer la découverte des apps locales (fiabilité sur Windows)
app.autodiscover_tasks(['app'])


@app.task(bind=True, ignore_result=True)
def debug_task(self):
    """Tâche de test — exécuter : celery -A core call core.celery.debug_task"""
    print(f'Request: {self.request!r}')
