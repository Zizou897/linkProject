from celery import shared_task
from django.utils import timezone
from datetime import timedelta


@shared_task
def cleanup_old_guest_forms_task():
    from .models import VozaviForm
    cutoff = timezone.now() - timedelta(hours=48)
    VozaviForm.objects.filter(user=None, created_at__lt=cutoff).delete()
