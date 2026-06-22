from datetime import timedelta
from django.contrib.auth.models import User
from django.db.models import Count, Q
from django.utils import timezone

from app.models import VozaviForm, VozaviResponse


def _daily_series(timestamps, days=30):
    """Liste de dicts {label, count, pct} par jour, du plus ancien au plus récent."""
    today = timezone.localdate()
    dates = [today - timedelta(days=i) for i in range(days - 1, -1, -1)]
    counts = {d: 0 for d in dates}
    for ts in timestamps:
        d = timezone.localtime(ts).date()
        if d in counts:
            counts[d] += 1
    peak = max(counts.values()) or 1
    return [{'label': d.strftime('%d/%m'), 'count': counts[d],
             'pct': round(counts[d] / peak * 100)} for d in dates]


def overview_context():
    customers = User.objects.filter(is_superuser=False)
    week = timezone.now() - timedelta(days=7)
    month = timezone.now() - timedelta(days=30)

    forms_agg = VozaviForm.objects.aggregate(
        total=Count('id'),
        draft=Count('id', filter=Q(status='draft')),
        active=Count('id', filter=Q(status='active')),
        closed=Count('id', filter=Q(status='closed')),
    )
    responses_total = VozaviResponse.objects.count()

    funnel = {
        'signed_up': customers.count(),
        'created': customers.filter(vozavi_forms__isnull=False).distinct().count(),
        'published': customers.filter(
            vozavi_forms__status__in=['active', 'closed']).distinct().count(),
        'with_response': customers.filter(
            vozavi_forms__responses__isnull=False).distinct().count(),
    }
    published_forms = (forms_agg['active'] or 0) + (forms_agg['closed'] or 0)
    publish_rate = round(published_forms / forms_agg['total'] * 100) if forms_agg['total'] else 0
    avg_resp = round(responses_total / forms_agg['total'], 1) if forms_agg['total'] else 0

    return {
        'users_total': customers.count(),
        'users_active_7d': customers.filter(last_login__gte=week).count(),
        'users_active_30d': customers.filter(last_login__gte=month).count(),
        'forms_total': forms_agg['total'],
        'forms_draft': forms_agg['draft'],
        'forms_active': forms_agg['active'],
        'forms_closed': forms_agg['closed'],
        'responses_total': responses_total,
        'publish_rate': publish_rate,
        'avg_responses': avg_resp,
        'funnel': funnel,
        'signups_series': _daily_series(
            customers.values_list('date_joined', flat=True), 30),
        'responses_series': _daily_series(
            VozaviResponse.objects.values_list('created_at', flat=True), 30),
    }
