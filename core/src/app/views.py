from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.db.models import Count
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.urls import reverse
from django.db import models as db_models
from django.utils import timezone
from datetime import timedelta

from .models import VozaviForm, Question, VozaviResponse, Answer
from .templates_data import FORM_TEMPLATES


# ── DASHBOARD ─────────────────────────────────────────────────────────────────

@login_required
def dashboard(request):
    forms_qs = VozaviForm.objects.filter(user=request.user).annotate(
        nb_responses=Count('responses', distinct=True),
    )
    total_forms = forms_qs.count()
    total_active = forms_qs.filter(status='active').count()
    total_responses = VozaviResponse.objects.filter(form__user=request.user).count()
    recent_forms = forms_qs.order_by('-updated_at')[:6]

    return render(request, 'app/admin/dashboard.html', {
        'total_forms': total_forms,
        'total_active': total_active,
        'total_responses': total_responses,
        'recent_forms': recent_forms,
    })


# ── AUTHENTIFICATION ──────────────────────────────────────────────────────────

def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')

    error = None
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')
        user = authenticate(request, username=username, password=password)
        if user is not None and user.is_active:
            login(request, user)
            next_url = request.POST.get('next') or request.GET.get('next') or 'dashboard'
            return redirect(next_url)
        else:
            error = "Identifiant ou mot de passe incorrect."

    return render(request, 'account/login.html', {'error': error})


def logout_view(request):
    logout(request)
    return redirect('login')


def signup_view(request):
    import secrets as _secrets
    from django.contrib.auth.models import User

    if request.user.is_authenticated:
        return redirect('dashboard')

    claim_pk = request.GET.get('claim') or request.POST.get('claim')
    error = None

    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        email = request.POST.get('email', '').strip().lower()
        password = request.POST.get('password1', '')

        if not username or not email or not password:
            error = "Veuillez renseigner tous les champs."
        elif len(password) < 8:
            error = "Le mot de passe doit contenir au moins 8 caractères."
        elif User.objects.filter(username=username).exists():
            error = "Cet identifiant est déjà utilisé."
        elif User.objects.filter(email=email).exists():
            error = "Un compte existe déjà avec cette adresse e-mail."
        else:
            user = User.objects.create_user(username=username, email=email, password=password, is_staff=True)
            login(request, user)

            # Claim and auto-publish the anonymous form if coming from builder
            if claim_pk:
                try:
                    anon_form = VozaviForm.objects.get(pk=int(claim_pk), user=None)
                    anon_form.user = user
                    if not anon_form.slug:
                        anon_form.slug = _secrets.token_urlsafe(8)
                    anon_form.status = 'active'
                    anon_form.save()
                    # Clear guest session key
                    request.session.pop('guest_form_pk', None)
                    return redirect('share_form', pk=anon_form.pk)
                except (VozaviForm.DoesNotExist, ValueError):
                    pass

            return redirect('dashboard')

    return render(request, 'account/signup.html', {'error': error, 'claim_pk': claim_pk})


# ── HOME ──────────────────────────────────────────────────────────────────────

def home(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    return render(request, 'vozavi/landing.html')


def custom_404(request, exception=None):
    return render(request, '404.html', status=404)


def contact_view(request):
    sent = False
    error = None
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        email = request.POST.get('email', '').strip()
        category = request.POST.get('category', '').strip()
        message = request.POST.get('message', '').strip()
        if not name or not email or not message:
            error = "Veuillez remplir tous les champs obligatoires."
        else:
            sent = True
    return render(request, 'vozavi/contact.html', {'sent': sent, 'error': error})


# ── VOZAVI FORM BUILDER ────────────────────────────────────────────────────────

def _guest_form_or_404(request, pk):
    """Return the VozaviForm if the requester (logged-in or guest session) owns it."""
    from django.http import Http404
    vform = get_object_or_404(VozaviForm, pk=pk)
    if request.user.is_authenticated:
        if vform.user_id != request.user.pk:
            raise Http404
    else:
        if request.session.get('guest_form_pk') != pk:
            raise Http404
    return vform


def _cleanup_old_guest_forms():
    """Delete unclaimed guest forms older than 48 h."""
    cutoff = timezone.now() - timedelta(hours=48)
    VozaviForm.objects.filter(user=None, created_at__lt=cutoff).delete()


def new_form(request):
    if request.method == 'POST':
        template_key = request.POST.get('template_key', 'scratch')
        tpl = FORM_TEMPLATES.get(template_key, FORM_TEMPLATES['scratch'])
        user = request.user if request.user.is_authenticated else None
        vform = VozaviForm.objects.create(
            user=user,
            title=tpl['title'],
            template_key=template_key,
            status='draft',
        )
        for i, q in enumerate(tpl['questions']):
            Question.objects.create(
                form=vform, type=q['type'], label=q['label'],
                required=q['required'], position=i, options=q['options'],
            )
        if user is None:
            request.session['guest_form_pk'] = vform.pk
            _cleanup_old_guest_forms()
        return redirect('edit_form', pk=vform.pk)
    return render(request, 'vozavi/builder/new.html')


def edit_form(request, pk):
    vform = _guest_form_or_404(request, pk)
    questions = vform.questions.order_by('position')
    is_guest = not request.user.is_authenticated
    return render(request, 'vozavi/builder/edit.html', {
        'vform': vform, 'questions': questions, 'is_guest': is_guest,
    })


def update_form_meta(request, pk):
    vform = _guest_form_or_404(request, pk)
    if request.method == 'POST':
        vform.title = request.POST.get('title', vform.title).strip() or vform.title
        vform.description = request.POST.get('description', vform.description).strip()
        vform.brand_name = request.POST.get('brand_name', vform.brand_name).strip()
        vform.brand_color = request.POST.get('brand_color', vform.brand_color)
        if 'logo' in request.FILES:
            vform.logo = request.FILES['logo']
        vform.save()
        return HttpResponse('<span class="save-ok">Enregistré ✓</span>')
    return HttpResponse(status=204)


def add_question(request, pk):
    vform = _guest_form_or_404(request, pk)
    if request.method == 'POST':
        q_type = request.POST.get('type', 'text')
        defaults = {
            'rating': ('Quelle note donneriez-vous ?', {'max': 5}),
            'single_choice': ('Choisissez une option', {'choices': ['Option 1', 'Option 2', 'Option 3']}),
            'multiple_choice': ("Sélectionnez tout ce qui s'applique", {'choices': ['Option 1', 'Option 2', 'Option 3']}),
            'text': ('Votre commentaire', {}),
            'grid': ('Évaluez les critères suivants', {'criteria': ['Critère 1', 'Critère 2', 'Critère 3'], 'max': 5}),
            'contact': ('Vos coordonnées', {'fields': ['first_name', 'email']}),
        }
        max_pos = vform.questions.aggregate(m=db_models.Max('position'))['m']
        label, options = defaults.get(q_type, ('Nouvelle question', {}))
        Question.objects.create(
            form=vform, type=q_type, label=label,
            required=False, position=(max_pos or 0) + 1, options=options,
        )
        questions = vform.questions.order_by('position')
        return render(request, 'vozavi/builder/partials/questions_list.html', {'vform': vform, 'questions': questions})
    return HttpResponse(status=405)


def update_question(request, pk, qid):
    vform = _guest_form_or_404(request, pk)
    q = get_object_or_404(Question, pk=qid, form=vform)
    if request.method == 'POST':
        label = request.POST.get('label', '').strip()
        if label:
            q.label = label
        q.required = request.POST.get('required') in ('on', 'true', '1')
        if q.type in ('single_choice', 'multiple_choice'):
            choices = [c.strip() for c in request.POST.getlist('choices') if c.strip()]
            if choices:
                q.options = {'choices': choices}
        elif q.type == 'grid':
            criteria = [c.strip() for c in request.POST.getlist('criteria') if c.strip()]
            if criteria:
                q.options = {**q.options, 'criteria': criteria}
        elif q.type == 'contact':
            _valid_keys = {'first_name', 'last_name', 'email', 'phone', 'company', 'job_title'}
            fields = [f for f in request.POST.getlist('contact_fields') if f in _valid_keys]
            q.options = {'fields': fields or ['email']}
        q.save()
        return render(request, 'vozavi/builder/partials/question_card.html', {'vform': vform, 'q': q})
    return HttpResponse(status=405)


def move_question(request, pk, qid):
    vform = _guest_form_or_404(request, pk)
    q = get_object_or_404(Question, pk=qid, form=vform)
    if request.method == 'POST':
        direction = request.POST.get('direction', 'down')
        qs = list(vform.questions.order_by('position'))
        idx = next((i for i, x in enumerate(qs) if x.pk == q.pk), None)
        if idx is not None:
            if direction == 'up' and idx > 0:
                qs[idx].position, qs[idx - 1].position = qs[idx - 1].position, qs[idx].position
                qs[idx].save()
                qs[idx - 1].save()
            elif direction == 'down' and idx < len(qs) - 1:
                qs[idx].position, qs[idx + 1].position = qs[idx + 1].position, qs[idx].position
                qs[idx].save()
                qs[idx + 1].save()
        questions = vform.questions.order_by('position')
        return render(request, 'vozavi/builder/partials/questions_list.html', {'vform': vform, 'questions': questions})
    return HttpResponse(status=405)


def delete_question(request, pk, qid):
    vform = _guest_form_or_404(request, pk)
    q = get_object_or_404(Question, pk=qid, form=vform)
    if request.method == 'POST':
        q.delete()
        return HttpResponse('')
    return HttpResponse(status=405)


def publish_form(request, pk):
    import secrets as _secrets
    vform = get_object_or_404(VozaviForm, pk=pk, user=request.user)
    if request.method == 'POST':
        if not vform.slug:
            vform.slug = _secrets.token_urlsafe(8)
        vform.status = 'active'
        vform.save()
        return redirect('share_form', pk=vform.pk)
    return HttpResponse(status=405)


@login_required
def share_form(request, pk):
    vform = get_object_or_404(VozaviForm, pk=pk, user=request.user)
    if vform.status == 'draft':
        return redirect('edit_form', pk=vform.pk)
    public_url = request.build_absolute_uri(reverse('public_form', args=[vform.slug]))
    return render(request, 'vozavi/builder/share.html', {'vform': vform, 'public_url': public_url})


@login_required
def qr_code_view(request, pk):
    import qrcode
    import io
    vform = get_object_or_404(VozaviForm, pk=pk, user=request.user)
    if not vform.slug:
        return HttpResponse(status=404)
    public_url = request.build_absolute_uri(reverse('public_form', args=[vform.slug]))
    qr = qrcode.QRCode(version=1, box_size=10, border=2)
    qr.add_data(public_url)
    qr.make(fit=True)
    img = qr.make_image(fill_color='#2C2C3A', back_color='white')
    buf = io.BytesIO()
    img.save(buf, format='PNG')
    buf.seek(0)
    return HttpResponse(buf.getvalue(), content_type='image/png')


def preview_form(request, pk):
    vform = _guest_form_or_404(request, pk)
    questions = vform.questions.order_by('position')
    return render(request, 'vozavi/public/form.html', {'vform': vform, 'questions': questions, 'preview': True})


def public_form(request, slug):
    vform = get_object_or_404(VozaviForm, slug=slug, status='active')
    questions = vform.questions.order_by('position')
    errors = {}
    if request.method == 'POST':
        response = VozaviResponse.objects.create(form=vform)
        valid = True
        for q in questions:
            field = f'q_{q.pk}'
            if q.type == 'multiple_choice':
                value = request.POST.getlist(field)
            elif q.type == 'rating':
                raw = request.POST.get(field, '')
                value = int(raw) if raw.isdigit() else 0
            elif q.type == 'contact':
                enabled = q.options.get('fields', ['email'])
                value = {k: request.POST.get(f'{field}_{k}', '').strip() for k in enabled}
                value = {k: v for k, v in value.items() if v}
            else:
                value = request.POST.get(field, '').strip()
            if q.required and not value:
                errors[str(q.pk)] = 'Ce champ est obligatoire.'
                valid = False
            else:
                Answer.objects.create(response=response, question=q, value=value)
        if valid:
            return redirect('public_form_thanks', slug=slug)
        response.delete()
    return render(request, 'vozavi/public/form.html', {'vform': vform, 'questions': questions, 'errors': errors})


def public_form_thanks(request, slug):
    vform = get_object_or_404(VozaviForm, slug=slug)
    return render(request, 'vozavi/public/thanks.html', {'vform': vform})


# ── DEMO ──────────────────────────────────────────────────────────────────────

def demo_form(request):
    if request.method == 'POST':
        return redirect('demo_form_thanks')
    return render(request, 'vozavi/public/demo.html')


def demo_form_thanks(request):
    return render(request, 'vozavi/public/demo_thanks.html')


# ── VOZAVI RESULTS ─────────────────────────────────────────────────────────────

def _compute_question_stats(q, values):
    if q.type == 'rating':
        mx = q.options.get('max', 5)
        nums = []
        for v in values:
            try:
                n = int(v)
                if 1 <= n <= mx:
                    nums.append(n)
            except (TypeError, ValueError):
                pass
        total = len(nums)
        if not total:
            return {'type': 'rating', 'count': 0, 'avg': None, 'dist': [], 'max': mx, 'avg_pct': 0, 'label': '—'}
        avg = round(sum(nums) / total, 1)
        dist = []
        for star in range(mx, 0, -1):
            cnt = nums.count(star)
            dist.append({'star': star, 'count': cnt, 'pct': round(cnt / total * 100)})
        if avg >= 4.5:
            qual = 'Excellent'
        elif avg >= 4.0:
            qual = 'Très bien'
        elif avg >= 3.0:
            qual = 'Bien'
        elif avg >= 2.0:
            qual = 'Passable'
        else:
            qual = 'À améliorer'
        return {'type': 'rating', 'count': total, 'avg': avg, 'avg_pct': round(avg / mx * 100), 'dist': dist, 'max': mx, 'label': qual}

    elif q.type in ('single_choice', 'multiple_choice'):
        choices = q.options.get('choices', [])
        counts_map = {c: 0 for c in choices}
        total_votes = 0
        for v in values:
            if q.type == 'multiple_choice' and isinstance(v, list):
                for item in v:
                    counts_map[item] = counts_map.get(item, 0) + 1
                    total_votes += 1
            elif isinstance(v, str) and v:
                counts_map[v] = counts_map.get(v, 0) + 1
                total_votes += 1
        choices_data = sorted(
            [{'label': c, 'count': counts_map.get(c, 0),
              'pct': round(counts_map.get(c, 0) / total_votes * 100) if total_votes else 0}
             for c in choices],
            key=lambda x: x['count'], reverse=True,
        )
        return {'type': q.type, 'count': len([v for v in values if v]), 'choices': choices_data, 'total_votes': total_votes}

    elif q.type == 'text':
        texts = [str(v).strip() for v in values if v and str(v).strip()]
        return {'type': 'text', 'count': len(texts), 'texts': texts}

    elif q.type == 'grid':
        criteria = q.options.get('criteria', [])
        texts = [str(v) for v in values if v]
        return {'type': 'grid', 'count': len(texts), 'criteria': criteria, 'texts': texts}

    elif q.type == 'contact':
        enabled = q.options.get('fields', ['email'])
        rows = []
        for v in values:
            if isinstance(v, dict) and v:
                rows.append(v)
        return {'type': 'contact', 'count': len(rows), 'fields': enabled, 'rows': rows}

    return {'type': q.type, 'count': 0}


def _fmt_answer(value):
    if isinstance(value, list):
        return ', '.join(str(v) for v in value)
    return str(value) if value is not None else ''


@login_required
def form_results(request, pk):
    from django.core.paginator import Paginator

    vform = get_object_or_404(VozaviForm, pk=pk, user=request.user)
    total = vform.responses.count()
    questions = list(vform.questions.order_by('position'))

    questions_data = []
    avg_sum = 0.0
    avg_weight = 0
    for q in questions:
        values = list(Answer.objects.filter(question=q).values_list('value', flat=True))
        stats = _compute_question_stats(q, values)
        questions_data.append({'q': q, 'stats': stats})
        if stats['type'] == 'rating' and stats.get('avg'):
            avg_sum += stats['avg'] * stats['count']
            avg_weight += stats['count']

    global_avg = round(avg_sum / avg_weight, 1) if avg_weight else None

    week_ago = timezone.now() - timedelta(days=7)
    neg_values = Answer.objects.filter(
        question__form=vform,
        question__type='rating',
        response__created_at__gte=week_ago,
    ).values_list('value', flat=True)
    negative_count = sum(1 for v in neg_values if isinstance(v, (int, float)) and v <= 2)

    last_response = vform.responses.order_by('-created_at').values_list('created_at', flat=True).first()

    return render(request, 'vozavi/builder/results.html', {
        'vform': vform,
        'total': total,
        'global_avg': global_avg,
        'global_avg_pct': round(global_avg / 5 * 100) if global_avg else 0,
        'questions_data': questions_data,
        'negative_count': negative_count,
        'last_response': last_response,
    })


@login_required
def form_responses(request, pk):
    from django.core.paginator import Paginator

    vform = get_object_or_404(VozaviForm, pk=pk, user=request.user)
    questions = list(vform.questions.order_by('position'))
    total = vform.responses.count()

    all_responses_qs = (
        vform.responses
        .prefetch_related('answers__question')
        .order_by('-created_at')
    )
    paginator = Paginator(all_responses_qs, 25)
    page_obj = paginator.get_page(request.GET.get('page', 1))

    response_rows = []
    for r in page_obj:
        ans_map = {a.question_id: a.value for a in r.answers.all()}
        cells = []
        has_negative = False
        for q in questions:
            raw = ans_map.get(q.pk)
            if raw is None:
                cells.append({'label': q.label, 'display': '—', 'type': q.type, 'raw': None})
            elif q.type == 'rating':
                try:
                    n = int(raw)
                    mx = q.options.get('max', 5)
                    if n <= 2:
                        has_negative = True
                    cells.append({'label': q.label, 'display': n, 'type': 'rating',
                                  'raw': n, 'max': mx, 'pct': round(n / mx * 100)})
                except (TypeError, ValueError):
                    cells.append({'label': q.label, 'display': '—', 'type': q.type, 'raw': None})
            else:
                cells.append({'label': q.label, 'display': _fmt_answer(raw), 'type': q.type, 'raw': raw})
        response_rows.append({'response': r, 'cells': cells, 'has_negative': has_negative})

    return render(request, 'vozavi/builder/responses.html', {
        'vform': vform,
        'total': total,
        'questions': questions,
        'page_obj': page_obj,
        'response_rows': response_rows,
    })


@login_required
def export_results_csv(request, pk):
    import csv as _csv
    vform = get_object_or_404(VozaviForm, pk=pk, user=request.user)
    questions = list(vform.questions.order_by('position'))

    resp = HttpResponse(content_type='text/csv; charset=utf-8-sig')
    resp['Content-Disposition'] = f'attachment; filename="resultats_{vform.slug or vform.pk}.csv"'

    writer = _csv.writer(resp)
    writer.writerow(['Date'] + [q.label for q in questions])
    for r in vform.responses.prefetch_related('answers__question').order_by('-created_at'):
        ans_map = {a.question_id: a.value for a in r.answers.all()}
        row = [r.created_at.strftime('%d/%m/%Y %H:%M')]
        for q in questions:
            row.append(_fmt_answer(ans_map.get(q.pk, '')))
        writer.writerow(row)
    return resp


@login_required
def export_results_excel(request, pk):
    import openpyxl
    from openpyxl.styles import Font, PatternFill, Alignment
    from openpyxl.utils import get_column_letter

    vform = get_object_or_404(VozaviForm, pk=pk, user=request.user)
    questions = list(vform.questions.order_by('position'))

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = 'Résultats'

    hdr_fill = PatternFill(start_color='4F46B8', end_color='4F46B8', fill_type='solid')
    hdr_font = Font(bold=True, color='FFFFFF', size=11)
    alt_fill = PatternFill(start_color='F4F3FB', end_color='F4F3FB', fill_type='solid')
    center = Alignment(horizontal='center', vertical='center', wrap_text=True)

    headers = ['Date'] + [q.label for q in questions]
    ws.append(headers)
    for col in range(1, len(headers) + 1):
        cell = ws.cell(1, col)
        cell.fill = hdr_fill
        cell.font = hdr_font
        cell.alignment = center
    ws.row_dimensions[1].height = 32

    for row_idx, r in enumerate(
        vform.responses.prefetch_related('answers__question').order_by('-created_at'), 2
    ):
        ans_map = {a.question_id: a.value for a in r.answers.all()}
        row_data = [r.created_at.strftime('%d/%m/%Y %H:%M')]
        for q in questions:
            row_data.append(_fmt_answer(ans_map.get(q.pk, '')))
        ws.append(row_data)
        if row_idx % 2 == 0:
            for col in range(1, len(headers) + 1):
                ws.cell(row_idx, col).fill = alt_fill
        ws.cell(row_idx, 1).alignment = Alignment(horizontal='center')

    for col_idx in range(1, len(headers) + 1):
        col_vals = [ws.cell(r, col_idx).value or '' for r in range(1, ws.max_row + 1)]
        best = max((len(str(v)) for v in col_vals), default=10)
        ws.column_dimensions[get_column_letter(col_idx)].width = min(max(best + 3, 14), 52)

    resp = HttpResponse(
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    resp['Content-Disposition'] = f'attachment; filename="resultats_{vform.slug or vform.pk}.xlsx"'
    wb.save(resp)
    return resp
