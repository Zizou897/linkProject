from django.contrib.auth.models import User
from django.core.cache import cache
from django.core.paginator import Paginator
from django.db.models import Count, Max, Q
from django.shortcuts import get_object_or_404, redirect, render
from django.http import HttpResponse

from app.models import ActivityEvent
from app.activity import log_event

from .decorators import superuser_required
from .kpis import overview_context


def _cached_overview():
    ctx = cache.get('bo_overview_ctx')
    if ctx is None:
        ctx = overview_context()
        cache.set('bo_overview_ctx', ctx, 10)   # cache 10 s
    return ctx


@superuser_required
def overview(request):
    ctx = _cached_overview()
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
    log_event('account_deactivated' if not target.is_active else 'user_login',
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


@superuser_required
def journal(request):
    return render(request, 'backoffice/stub.html', {'active': 'journal', 'heading': 'Journal'})


@superuser_required
def health(request):
    return render(request, 'backoffice/stub.html', {'active': 'health', 'heading': 'Santé technique'})
