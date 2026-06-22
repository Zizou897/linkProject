import logging
from celery import shared_task
from django.utils import timezone
from datetime import timedelta

logger = logging.getLogger(__name__)


@shared_task
def cleanup_old_guest_forms_task():
    from .models import VozaviForm
    cutoff = timezone.now() - timedelta(hours=48)
    VozaviForm.objects.filter(user=None, created_at__lt=cutoff).delete()


def send_new_response_email(form_id, results_url):
    """Envoie au créateur l'e-mail de notification (logique réutilisable, synchrone).

    Appelée en arrière-plan via after_response (voir views), ou par la tâche Celery.
    """
    from django.conf import settings
    from django.core.mail import send_mail
    from django.template.loader import render_to_string
    from .models import VozaviForm

    try:
        vform = VozaviForm.objects.select_related('user').get(pk=form_id)
    except VozaviForm.DoesNotExist:
        return

    # On ne notifie que si : option activée, propriétaire connu, e-mail renseigné.
    if not vform.notify_responses or not vform.user or not vform.user.email:
        return

    nb = vform.responses.count()
    context = {
        'vform': vform,
        'nb_responses': nb,
        'results_url': results_url,
        'user': vform.user,
    }
    subject = f"Nouvelle réponse — {vform.title}"
    html = render_to_string('emails/new_response.html', context)
    text = (
        f"Bonjour,\n\nVous avez reçu une nouvelle réponse sur votre formulaire "
        f"« {vform.title} » (total : {nb}).\n\nConsultez les réponses : {results_url}\n\n"
        f"— L'équipe Vozavi"
    )
    try:
        send_mail(subject, text, settings.DEFAULT_FROM_EMAIL,
                  [vform.user.email], html_message=html, fail_silently=False)
        from .activity import log_event
        log_event('email_sent', actor=vform.user, target=vform, label=vform.title)
    except Exception as e:
        logger.error(f"Échec notification nouvelle réponse (form {form_id}): {e}")
        from .activity import log_event
        log_event('email_failed', actor=vform.user, target=vform, label=vform.title,
                  success=False, error=str(e)[:200])


@shared_task
def notify_new_response_task(form_id, results_url):
    """Variante Celery de la notification (utilisable pour des envois planifiés)."""
    send_new_response_email(form_id, results_url)


@shared_task
def cleanup_old_events(days=180):
    """Purge les ActivityEvent plus vieux que `days` jours."""
    from .models import ActivityEvent
    cutoff = timezone.now() - timedelta(days=days)
    ActivityEvent.objects.filter(created_at__lt=cutoff).delete()
