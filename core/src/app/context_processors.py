from django.conf import settings


def site_settings(request):
    """Expose des réglages site-wide aux templates.

    - GA_MEASUREMENT_ID : identifiant Google Analytics 4 (vide = pas de suivi).
    """
    return {
        'GA_MEASUREMENT_ID': settings.GA_MEASUREMENT_ID,
    }
