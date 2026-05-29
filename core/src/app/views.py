from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.db.models import Count, Q, Exists, OuterRef
from django.contrib.admin.views.decorators import staff_member_required

from .models import LienSecurise, Formation, SessionPresentielle, Avis
from .forms import SessionPresentielleForm, FormationForm, AvisForm


# ── HELPERS ───────────────────────────────────────────────────────────────────

def _active_sessions_subquery():
    """Sous-requête : sessions dont le lien est actif et non expiré."""
    return SessionPresentielle.objects.filter(
        formation=OuterRef('pk'),
        lien__actif=True,
    ).filter(
        Q(lien__date_expiration__isnull=True) |
        Q(lien__date_expiration__gt=timezone.now())
    )

# ── DASHBOARD ADMINISTRATEUR ──────────────────────────────────────────────────

@staff_member_required
def dashboard(request):
    formations = Formation.objects.filter(archive=False).annotate(
        nb_avis=Count('sessions__avis', distinct=True),
        nb_sessions=Count('sessions', distinct=True),
        est_active=Exists(_active_sessions_subquery()),
    ).order_by('-nb_avis')

    total_formations_all = Formation.objects.count()
    total_formations = Formation.objects.filter(archive=False).count()
    total_sessions = SessionPresentielle.objects.count()
    total_avis = Avis.objects.count()

    avis_recents = Avis.objects.select_related('session__formation').order_by('-created_at')[:10]

    geo = (
        Avis.objects
        .exclude(zone_geographique='')
        .values('zone_geographique')
        .annotate(total=Count('id'))
        .order_by('-total')[:10]
    )

    return render(request, 'app/admin/dashboard.html', {
        'formations': formations,
        'total_formations_all': total_formations_all,
        'total_formations': total_formations,
        'total_sessions': total_sessions,
        'total_avis': total_avis,
        'avis_recents': avis_recents,
        'geo': geo,
    })


# ── MODULE SESSIONS PRÉSENTIEL ────────────────────────────────────────────────

@staff_member_required
def sessions_liste(request):
    sessions = (
        SessionPresentielle.objects
        .select_related('formation')
        .annotate(
            nb_avis=Count('avis', distinct=True),
        )
        .order_by('-date')
    )
    return render(request, 'app/sessions/liste.html', {'sessions': sessions})


@staff_member_required
def session_detail(request, pk):
    session = get_object_or_404(SessionPresentielle.objects.select_related('formation', 'lien'), pk=pk)
    avis_list = session.avis.order_by('-created_at')
    return render(request, 'app/sessions/detail.html', {
        'session': session,
        'avis_list': avis_list,
    })


def _generer_lien_session(session, request, date_expiration=None):
    """Crée un LienSecurise lié à la formation de la session et l'attache à la session."""
    from datetime import timedelta, datetime
    if date_expiration:
        expiration = timezone.make_aware(datetime.combine(date_expiration, datetime.min.time()))
    else:
        expiration = timezone.now() + timedelta(days=90)
    lien = LienSecurise.objects.create(
        label=f"Session — {session.formation.libelle} ({session.date.strftime('%d/%m/%Y')})",
        actif=True,
        date_expiration=expiration,
    )
    lien.formations.add(session.formation)
    session.lien = lien
    session.save(update_fields=['lien'])
    return lien


@staff_member_required
def session_creer(request, formation_pk=None):
    formation = get_object_or_404(Formation, pk=formation_pk) if formation_pk else None
    initial = {'formation': formation} if formation else {}
    form = SessionPresentielleForm(request.POST or None, initial=initial)
    if form.is_valid():
        session = form.save()
        date_expiration = form.cleaned_data.get('date_expiration_lien')
        _generer_lien_session(session, request, date_expiration=date_expiration)
        messages.success(request, 'Session créée avec son lien sécurisé.')
        return redirect('formation_detail', pk=session.formation.pk)
    return render(request, 'app/sessions/form.html', {
        'form': form,
        'titre': 'Créer une session',
        'formation': formation,
    })


@staff_member_required
def session_modifier(request, pk):
    session = get_object_or_404(SessionPresentielle, pk=pk)
    form = SessionPresentielleForm(request.POST or None, instance=session)
    if form.is_valid():
        form.save()
        messages.success(request, 'Session mise à jour.')
        return redirect('formation_detail', pk=session.formation.pk)
    return render(request, 'app/sessions/form.html', {
        'form': form,
        'titre': 'Modifier la session',
        'session': session,
    })


@staff_member_required
def regenerer_lien(request, pk):
    """Regénère le LienSecurise d'une session (désactive l'ancien, crée un nouveau)."""
    session = get_object_or_404(SessionPresentielle, pk=pk)
    if session.lien:
        session.lien.actif = False
        session.lien.save(update_fields=['actif'])
        session.lien = None
        session.save(update_fields=['lien'])
    _generer_lien_session(session, request)
    messages.success(request, 'Nouveau lien sécurisé généré.')
    return redirect('session_detail', pk=pk)


@staff_member_required
def cloturer_session(request, pk):
    session = get_object_or_404(SessionPresentielle, pk=pk)
    if request.method == 'POST':
        nouveau_statut = request.POST.get('statut', SessionPresentielle.Statut.CLOTUREE)
        session.statut = nouveau_statut
        session.save()
        messages.success(request, f'Session marquée comme « {session.get_statut_display()} ».')
        return redirect('session_detail', pk=pk)
    return render(request, 'app/sessions/cloturer.html', {'session': session})


# ── GESTION DES FORMATIONS ───────────────────────────────────────────────────

@staff_member_required
def formations_liste(request):
    voir_archivees = request.GET.get('archive') == '1'
    base_qs = Formation.objects.annotate(
        nb_sessions=Count('sessions', distinct=True),
        nb_avis=Count('sessions__avis', distinct=True),
        est_active=Exists(_active_sessions_subquery()),
    )
    formations = base_qs.filter(archive=voir_archivees).order_by('-created_at')
    nb_archivees = Formation.objects.filter(archive=True).count()
    return render(request, 'app/formations/liste.html', {
        'formations': formations,
        'voir_archivees': voir_archivees,
        'nb_archivees': nb_archivees,
    })


@staff_member_required
def formation_creer(request):
    form = FormationForm(request.POST or None)
    if form.is_valid():
        form.save()
        messages.success(request, 'Formation créée avec succès.')
        return redirect('formations_liste')
    return render(request, 'app/formations/form.html', {'form': form, 'titre': 'Nouvelle formation'})


@staff_member_required
def formation_modifier(request, pk):
    formation = get_object_or_404(Formation, pk=pk)
    form = FormationForm(request.POST or None, instance=formation)
    if form.is_valid():
        form.save()
        messages.success(request, 'Formation mise à jour.')
        return redirect('formations_liste')
    return render(request, 'app/formations/form.html', {
        'form': form,
        'titre': 'Modifier la formation',
        'formation': formation,
    })


@staff_member_required
def formation_detail(request, pk):
    formation = get_object_or_404(Formation, pk=pk)
    sessions = (
        formation.sessions
        .annotate(nb_avis=Count('avis'))
        .order_by('-date')
    )
    total_avis = Avis.objects.filter(session__formation=formation).count()
    sessions_actives = formation.sessions.filter(
        lien__actif=True
    ).filter(
        Q(lien__date_expiration__isnull=True) | Q(lien__date_expiration__gt=timezone.now())
    ).count()
    return render(request, 'app/formations/detail.html', {
        'formation': formation,
        'sessions': sessions,
        'total_avis': total_avis,
        'sessions_actives': sessions_actives,
    })


@staff_member_required
def formation_supprimer(request, pk):
    formation = get_object_or_404(Formation, pk=pk)
    if request.method == 'POST':
        formation.delete()
        messages.success(request, f'La formation « {formation.libelle} » a été supprimée.')
        return redirect('formations_liste')
    return render(request, 'app/formations/supprimer.html', {'formation': formation})


@staff_member_required
def formation_archiver(request, pk):
    formation = get_object_or_404(Formation, pk=pk)
    formation.archive = not formation.archive
    formation.save(update_fields=['archive'])

    # Activer/désactiver les liens de toutes les sessions de la formation
    liens = LienSecurise.objects.filter(session__formation=formation)
    if formation.archive:
        liens.update(actif=False)
    else:
        # Réactiver uniquement les liens non expirés
        liens.filter(
            Q(date_expiration__isnull=True) | Q(date_expiration__gt=timezone.now())
        ).update(actif=True)

    statut = 'archivée' if formation.archive else 'désarchivée'
    messages.success(request, f'Formation « {formation.libelle} » {statut}.')
    return redirect('formations_liste')


# ── MODULE AVIS (public) ─────────────────────────────────────────────────────

def avis_formation(request, token):
    """Formulaire public d'avis/intérêt pour une formation, accessible via le lien de session."""
    lien = LienSecurise.objects.filter(token=token, actif=True).first()
    if not lien:
        return render(request, 'app/avis/lien_invalide.html', {})
    if lien.date_expiration and lien.date_expiration < timezone.now():
        return render(request, 'app/avis/lien_invalide.html', {})

    try:
        session = lien.session
    except Exception:
        return render(request, 'app/avis/lien_invalide.html', {})

    formation = session.formation

    if request.method == 'POST':
        form = AvisForm(request.POST)
        if form.is_valid():
            avis = form.save(commit=False)
            avis.session = session
            avis.save()
            return redirect('avis_confirmation', token=token)
    else:
        form = AvisForm()

    return render(request, 'app/avis/formulaire.html', {
        'formation': formation,
        'session': session,
        'form': form,
    })


def avis_confirmation(request, token):
    lien = LienSecurise.objects.filter(token=token).first()
    formation = lien.session.formation if lien and hasattr(lien, 'session') else None
    return render(request, 'app/avis/confirmation.html', {'formation': formation})


# ── AUTHENTIFICATION ADMIN ────────────────────────────────────────────────────

def login_view(request):
    if request.user.is_authenticated and request.user.is_staff:
        return redirect('dashboard')

    error = None
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')
        user = authenticate(request, username=username, password=password)
        if user is not None and user.is_staff:
            login(request, user)
            next_url = request.GET.get('next', 'dashboard')
            return redirect(next_url)
        elif user is not None and not user.is_staff:
            error = "Votre compte n'a pas les droits d'accès au tableau de bord."
        else:
            error = "Identifiant ou mot de passe incorrect."

    return render(request, 'app/auth/login.html', {'error': error})


def logout_view(request):
    logout(request)
    return redirect('login')


# ── HOME ──────────────────────────────────────────────────────────────────────

def home(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    return redirect('login')
