from django import template

from app.models import ContactMessage

register = template.Library()


@register.simple_tag
def bo_unread_contacts():
    """Nombre de messages de contact non lus (badge du rail)."""
    return ContactMessage.objects.filter(is_read=False).count()


# Tonalité visuelle par famille d'événement (badge du journal).
EVENT_TONES = {
    'response_received': 'pos',
    'form_published': 'pos',
    'guest_form_claimed': 'pos',
    'email_sent': 'pos',
    'account_deactivated': 'warn',
    'form_closed': 'warn',
    'email_failed': 'neg',
    'account_deleted': 'neg',
    'account_deleted_by_admin': 'neg',
    'form_deleted': 'neg',
    'user_signup': 'info',
    'contact_message': 'info',
    'form_created': 'info',
}


@register.filter
def event_tone(event_type):
    return EVENT_TONES.get(event_type, 'neutral')


@register.filter
def hue(pk):
    """Classe de teinte stable (h1…h6) pour un avatar, dérivée de la pk."""
    try:
        return f'h{int(pk) % 6 + 1}'
    except (TypeError, ValueError):
        return 'h1'
