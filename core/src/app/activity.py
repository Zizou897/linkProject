import logging
from django.contrib.auth.signals import user_logged_in, user_logged_out
from django.dispatch import receiver

logger = logging.getLogger(__name__)


def _client_ip(request):
    if request is None:
        return None
    fwd = request.META.get('HTTP_X_FORWARDED_FOR', request.META.get('REMOTE_ADDR', ''))
    return (fwd.split(',')[0].strip() or None)


def log_event(event_type, *, actor=None, target=None, label='', success=True,
              request=None, **metadata):
    """Enregistre un ActivityEvent. NE LÈVE JAMAIS : la journalisation ne doit
    jamais casser la requête produit."""
    from .models import ActivityEvent
    try:
        ip = _client_ip(request)
        if actor is None and request is not None:
            u = getattr(request, 'user', None)
            if u is not None and getattr(u, 'is_authenticated', False):
                actor = u
        target_type, target_id = '', None
        if target is not None:
            target_type = target.__class__.__name__.lower()
            target_id = target.pk
            if not label:
                label = str(target)[:255]
        ActivityEvent.objects.create(
            event_type=event_type, actor=actor, target_type=target_type,
            target_id=target_id, label=label[:255], success=success,
            ip=ip, metadata=metadata or {},
        )
    except Exception:
        logger.exception("log_event a échoué (event_type=%s)", event_type)


@receiver(user_logged_in)
def _on_login(sender, request, user, **kwargs):
    log_event('user_login', actor=user, request=request, label=user.get_username())


@receiver(user_logged_out)
def _on_logout(sender, request, user, **kwargs):
    if user is not None:
        log_event('user_logout', actor=user, request=request, label=user.get_username())
