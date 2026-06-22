from datetime import timedelta

from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.core.cache import cache
from django.core.paginator import Paginator
from django.db.models import Count, Max, Q
from django.shortcuts import get_object_or_404, redirect, render
from django.http import HttpResponse
from django.urls import reverse
from django.utils import timezone
from django.utils.http import url_has_allowed_host_and_scheme

from app.models import ActivityEvent, ContactMessage, VozaviForm
from app.activity import log_event

from .decorators import superuser_required
from .kpis import overview_context


# ── AUTHENTIFICATION ADMIN ─────────────────────────────────────────────────────

def bo_login(request):
    """Connexion dédiée au back-office : super-utilisateurs uniquement."""
    if request.user.is_authenticated and request.user.is_superuser:
        return redirect('bo_overview')

    error = None
    if request.method == 'POST':
        ip = (request.META.get('HTTP_X_FORWARDED_FOR',
                               request.META.get('REMOTE_ADDR', '')) or '').split(',')[0].strip()
        rate_key = f'bo_login_attempts_{ip}'
        attempts = cache.get(rate_key, 0)
        if attempts >= 5:
            return render(request, 'backoffice/login.html', {
                'error': "Trop de tentatives. Réessayez dans 15 minutes.",
                'next': request.POST.get('next', ''),
            })

        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')
        user = authenticate(request, username=username, password=password)
        if user is not None and user.is_active and user.is_superuser:
            cache.delete(rate_key)
            login(request, user)
            next_url = request.POST.get('next') or request.GET.get('next')
            if not url_has_allowed_host_and_scheme(next_url, allowed_hosts={request.get_host()}):
                next_url = reverse('bo_overview')
            return redirect(next_url)

        cache.set(rate_key, attempts + 1, 900)
        error = "Identifiants invalides ou accès non autorisé."

    return render(request, 'backoffice/login.html', {
        'error': error, 'next': request.GET.get('next', request.POST.get('next', '')),
    })


def bo_logout(request):
    """Déconnexion du back-office (POST) → écran de connexion admin."""
    if request.method == 'POST':
        logout(request)
    return redirect('bo_login')


def _cached_overview():
    ctx = cache.get('bo_overview_ctx')
    if ctx is None:
        ctx = overview_context()
        cache.set('bo_overview_ctx', ctx, 10)   # cache 10 s
    return ctx


@superuser_required
def overview(request):
    ctx = dict(_cached_overview())
    ctx['active'] = 'overview'
    return render(request, 'backoffice/overview.html', ctx)


@superuser_required
def kpis_partial(request):
    return render(request, 'backoffice/partials/kpis.html', _cached_overview())


@superuser_required
def users_list(request):
    qs = User.objects.filter(is_superuser=False).annotate(
        nb_forms=Count('vozavi_forms', distinct=True),
        nb_responses=Count('vozavi_forms__responses', distinct=True),
        last_activity=Max('vozavi_forms__updated_at'),
    )
    q = request.GET.get('q', '').strip()
    if q:
        qs = qs.filter(Q(username__icontains=q) | Q(email__icontains=q))
    qs = qs.order_by('-date_joined')
    page = Paginator(qs, 25).get_page(request.GET.get('page'))
    return render(request, 'backoffice/users.html',
                  {'active': 'users', 'page_obj': page, 'q': q})


def _protected(request, target):
    """True si la cible ne peut pas être modifiée (soi-même ou autre super-admin)."""
    return target.pk == request.user.pk or target.is_superuser


@superuser_required
def user_detail(request, pk):
    target = get_object_or_404(User, pk=pk)
    forms = target.vozavi_forms.annotate(nb=Count('responses', distinct=True)).order_by('-updated_at')
    events = ActivityEvent.objects.filter(actor=target)[:50]
    return render(request, 'backoffice/user_detail.html', {
        'active': 'users', 'target': target, 'forms': forms, 'events': events,
        'protected': _protected(request, target),
    })


@superuser_required
def user_toggle_active(request, pk):
    if request.method != 'POST':
        return HttpResponse(status=405)
    target = get_object_or_404(User, pk=pk)
    if _protected(request, target):
        return redirect('bo_user_detail', pk=pk)
    target.is_active = not target.is_active
    target.save(update_fields=['is_active'])
    log_event('account_deactivated' if not target.is_active else 'account_reactivated',
              actor=request.user, request=request, label=target.get_username(),
              now_active=target.is_active)
    return redirect('bo_user_detail', pk=pk)


@superuser_required
def user_delete(request, pk):
    target = get_object_or_404(User, pk=pk)
    if _protected(request, target):
        return redirect('bo_user_detail', pk=pk)
    if request.method == 'POST':
        username = target.get_username()
        target.delete()
        log_event('account_deleted_by_admin', actor=request.user, request=request,
                  label=username)
        return redirect('bo_users')
    return render(request, 'backoffice/user_detail.html', {
        'active': 'users', 'target': target, 'confirm_delete': True,
        'forms': target.vozavi_forms.all(), 'events': [],
        'protected': _protected(request, target),
    })


def _journal_qs(request):
    qs = ActivityEvent.objects.select_related('actor')
    etype = request.GET.get('type', '').strip()
    if etype:
        qs = qs.filter(event_type=etype)
    q = request.GET.get('q', '').strip()
    if q:
        qs = qs.filter(Q(actor__username__icontains=q) | Q(actor__email__icontains=q)
                       | Q(label__icontains=q))
    return qs


@superuser_required
def journal(request):
    page = Paginator(_journal_qs(request), 50).get_page(request.GET.get('page'))
    return render(request, 'backoffice/journal.html', {
        'active': 'journal', 'page_obj': page,
        'type': request.GET.get('type', ''), 'q': request.GET.get('q', ''),
        'event_types': ActivityEvent.EVENT_CHOICES,
    })


@superuser_required
def journal_feed(request):
    events = _journal_qs(request)[:40]
    return render(request, 'backoffice/partials/feed.html', {'events': events})


@superuser_required
def health(request):
    since48 = timezone.now() - timedelta(hours=48)
    ctx = {
        'active': 'health',
        'emails_sent': ActivityEvent.objects.filter(event_type='email_sent').count(),
        'emails_failed': ActivityEvent.objects.filter(event_type='email_failed').count(),
        'contacts_unread': ContactMessage.objects.filter(is_read=False).count(),
        'guest_forms': VozaviForm.objects.filter(user=None, created_at__gte=since48).count(),
        'recent_failures': ActivityEvent.objects.filter(success=False)[:20],
    }
    return render(request, 'backoffice/health.html', ctx)
