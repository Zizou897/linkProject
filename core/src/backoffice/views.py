from django.core.cache import cache
from django.shortcuts import render

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
    return render(request, 'backoffice/stub.html', {'active': 'users', 'heading': 'Utilisateurs'})


@superuser_required
def journal(request):
    return render(request, 'backoffice/stub.html', {'active': 'journal', 'heading': 'Journal'})


@superuser_required
def health(request):
    return render(request, 'backoffice/stub.html', {'active': 'health', 'heading': 'Santé technique'})
