from functools import wraps
from django.contrib.auth.views import redirect_to_login
from django.http import Http404


def superuser_required(view):
    """Anonyme → connexion ; authentifié non-superadmin → 404 (pas de divulgation)."""
    @wraps(view)
    def _wrapped(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect_to_login(request.get_full_path())
        if not request.user.is_superuser:
            raise Http404
        return view(request, *args, **kwargs)
    return _wrapped
