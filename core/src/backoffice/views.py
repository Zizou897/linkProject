from django.contrib.auth.models import User
from django.core.cache import cache
from django.core.paginator import Paginator
from django.db.models import Count, Max, Q
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


@superuser_required
def user_detail(request, pk):
    return render(request, 'backoffice/stub.html', {'active': 'users', 'heading': 'Fiche utilisateur'})


@superuser_required
def journal(request):
    return render(request, 'backoffice/stub.html', {'active': 'journal', 'heading': 'Journal'})


@superuser_required
def health(request):
    return render(request, 'backoffice/stub.html', {'active': 'health', 'heading': 'Santé technique'})
