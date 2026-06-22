# Back-office d'observabilité — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Doter Vozavi d'un back-office super-utilisateur (`/admin-vozavi/`) : KPI/funnel, liste & fiches utilisateurs, journal d'événements temps réel, santé technique, et actions (désactiver/supprimer un compte).

**Architecture:** Le cœur (`app/`) gagne un modèle `ActivityEvent` + un helper `log_event()` appelé aux points clés. Une nouvelle app `backoffice/` en lecture sert les 4 surfaces, réservée aux super-utilisateurs, rafraîchie par polling HTMX.

**Tech Stack:** Django 5.2, templates + HTMX (CDN), `vozavi.css` (tokens existants), tests `unittest` via `manage.py test`. Pas de librairie de graphiques (barres CSS/SVG inline).

**Référence spec :** `docs/superpowers/specs/2026-06-22-backoffice-observabilite-design.md`

---

## Conventions

**Commande de test** (toujours depuis `core/src/`, le runner force `DEBUG=False` mais on passe les variables d'env requises) :

```bash
cd core/src && DEBUG=True SECRET_KEY=test ../../venv/Scripts/python.exe manage.py test <label> -v 2
```

Sous Windows/Git-Bash, `../../venv/Scripts/python.exe` est l'interpréteur du projet. Remplacer `<label>` par `app.tests.ClasseDeTest` ou `backoffice`.

**Note migration statique en test :** déjà géré dans `core/settings.py` (`if 'test' in sys.argv` bascule sur un stockage sans manifeste).

---

## File Structure

| Fichier | Responsabilité |
|---|---|
| `core/src/app/models.py` (modif) | + modèle `ActivityEvent` |
| `core/src/app/migrations/0015_activityevent.py` (créé) | migration du modèle |
| `core/src/app/activity.py` (créé) | helper `log_event` + récepteurs de signaux auth |
| `core/src/app/apps.py` (modif) | `ready()` connecte les signaux |
| `core/src/app/views.py` (modif) | appels `log_event` dans les vues produit |
| `core/src/app/tasks.py` (modif) | `log_event` e-mail envoyé/échoué |
| `core/src/app/tests.py` (modif) | tests d'instrumentation |
| `core/src/backoffice/` (créé) | nouvelle app : `apps.py`, `decorators.py`, `kpis.py`, `views.py`, `urls.py`, `tests.py` |
| `core/src/backoffice/templates/backoffice/*.html` (créés) | chrome + 4 surfaces + partials |
| `core/src/core/settings.py` (modif) | `'backoffice'` dans `LOCAL_APPS` |
| `core/src/core/urls.py` (modif) | `include('backoffice.urls')` |

---

## Task 1 : Modèle `ActivityEvent`

**Files:**
- Modify: `core/src/app/models.py` (ajout en fin de fichier)
- Test: `core/src/app/tests.py`

- [ ] **Step 1 : Écrire le test qui échoue**

Ajouter à la fin de `core/src/app/tests.py` :

```python
class ActivityEventModelTests(TestCase):
    def test_event_creation_and_defaults(self):
        from .models import ActivityEvent
        e = ActivityEvent.objects.create(event_type='form_created', label='Resto')
        self.assertTrue(e.success)            # succès par défaut
        self.assertIsNone(e.actor)            # acteur facultatif
        self.assertEqual(e.metadata, {})      # JSON par défaut
        self.assertIsNotNone(e.created_at)
```

- [ ] **Step 2 : Lancer le test, vérifier l'échec**

Run: `cd core/src && DEBUG=True SECRET_KEY=test ../../venv/Scripts/python.exe manage.py test app.tests.ActivityEventModelTests -v 2`
Expected: FAIL — `ImportError: cannot import name 'ActivityEvent'`.

- [ ] **Step 3 : Ajouter le modèle**

À la fin de `core/src/app/models.py` :

```python
# ── JOURNALISATION (back-office) ──────────────────────────────────────────────

class ActivityEvent(models.Model):
    EVENT_CHOICES = [
        ('user_signup', 'Inscription'),
        ('user_login', 'Connexion'),
        ('user_logout', 'Déconnexion'),
        ('account_deleted', 'Compte supprimé'),
        ('guest_form_claimed', 'Formulaire invité réclamé'),
        ('form_created', 'Formulaire créé'),
        ('form_published', 'Formulaire publié'),
        ('form_closed', 'Formulaire fermé'),
        ('form_reopened', 'Formulaire rouvert'),
        ('form_duplicated', 'Formulaire dupliqué'),
        ('form_deleted', 'Formulaire supprimé'),
        ('response_received', 'Réponse reçue'),
        ('contact_message', 'Message de contact'),
        ('email_sent', 'E-mail envoyé'),
        ('email_failed', 'E-mail échoué'),
        ('account_deactivated', 'Compte désactivé (admin)'),
        ('account_deleted_by_admin', 'Compte supprimé (admin)'),
    ]
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    event_type = models.CharField(max_length=40, choices=EVENT_CHOICES, db_index=True)
    actor = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL,
                              related_name='activity_events')
    target_type = models.CharField(max_length=40, blank=True)
    target_id = models.PositiveIntegerField(null=True, blank=True)
    label = models.CharField(max_length=255, blank=True)
    success = models.BooleanField(default=True)
    ip = models.GenericIPAddressField(null=True, blank=True)
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['event_type', 'created_at']),
            models.Index(fields=['actor', 'created_at']),
        ]

    def __str__(self):
        return f"{self.event_type} · {self.label or self.actor or '—'}"
```

- [ ] **Step 4 : Générer la migration**

Run: `cd core/src && DEBUG=True SECRET_KEY=test ../../venv/Scripts/python.exe manage.py makemigrations app`
Expected: crée `app/migrations/0015_activityevent.py`.

- [ ] **Step 5 : Lancer le test, vérifier le succès**

Run: `cd core/src && DEBUG=True SECRET_KEY=test ../../venv/Scripts/python.exe manage.py test app.tests.ActivityEventModelTests -v 2`
Expected: PASS.

- [ ] **Step 6 : Commit**

```bash
git add core/src/app/models.py core/src/app/migrations/0015_activityevent.py core/src/app/tests.py
git commit -m "Back-office : modèle ActivityEvent (journalisation)"
```

---

## Task 2 : Helper `log_event`

**Files:**
- Create: `core/src/app/activity.py`
- Test: `core/src/app/tests.py`

- [ ] **Step 1 : Écrire le test qui échoue**

Ajouter à `core/src/app/tests.py` :

```python
class LogEventTests(TestCase):
    def test_log_event_creates_record_with_target_and_ip(self):
        from .activity import log_event
        from .models import ActivityEvent, VozaviForm
        f = VozaviForm.objects.create(title='Resto', status='draft')

        class FakeReq:
            META = {'REMOTE_ADDR': '10.0.0.5'}
            class user:  # anonyme
                is_authenticated = False
        log_event('form_created', target=f, request=FakeReq)

        e = ActivityEvent.objects.get()
        self.assertEqual(e.event_type, 'form_created')
        self.assertEqual(e.target_type, 'vozaviform')
        self.assertEqual(e.target_id, f.pk)
        self.assertEqual(e.label, 'Resto')
        self.assertEqual(e.ip, '10.0.0.5')

    def test_log_event_never_raises(self):
        from .activity import log_event
        # event_type invalide / metadata non sérialisable : ne doit pas lever
        log_event('form_created', metadata={'x': object()})
        # le test réussit simplement s'il n'y a pas d'exception
```

- [ ] **Step 2 : Lancer le test, vérifier l'échec**

Run: `cd core/src && DEBUG=True SECRET_KEY=test ../../venv/Scripts/python.exe manage.py test app.tests.LogEventTests -v 2`
Expected: FAIL — `ModuleNotFoundError: No module named 'app.activity'`.

- [ ] **Step 3 : Créer le helper**

`core/src/app/activity.py` :

```python
import logging
from django.contrib.auth.signals import user_logged_in, user_logged_out
from django.dispatch import receiver

logger = logging.getLogger(__name__)


def _client_ip(request):
    if request is None:
        return None
    fwd = request.META.get('HTTP_X_FORWARDED_FOR', request.META.get('REMOTE_ADDR', ''))
    return (fwd.split(',')[0].strip() or None)


def log_event(event_type, *, actor=None, target=None, label='', success=True,
              request=None, **metadata):
    """Enregistre un ActivityEvent. NE LÈVE JAMAIS : la journalisation ne doit
    jamais casser la requête produit."""
    from .models import ActivityEvent
    try:
        ip = _client_ip(request)
        if actor is None and request is not None:
            u = getattr(request, 'user', None)
            if u is not None and getattr(u, 'is_authenticated', False):
                actor = u
        target_type, target_id = '', None
        if target is not None:
            target_type = target.__class__.__name__.lower()
            target_id = target.pk
            if not label:
                label = str(target)[:255]
        ActivityEvent.objects.create(
            event_type=event_type, actor=actor, target_type=target_type,
            target_id=target_id, label=label[:255], success=success,
            ip=ip, metadata=metadata or {},
        )
    except Exception:
        logger.exception("log_event a échoué (event_type=%s)", event_type)


@receiver(user_logged_in)
def _on_login(sender, request, user, **kwargs):
    log_event('user_login', actor=user, request=request, label=user.get_username())


@receiver(user_logged_out)
def _on_logout(sender, request, user, **kwargs):
    if user is not None:
        log_event('user_logout', actor=user, request=request, label=user.get_username())
```

Note : `metadata={'x': object()}` n'est pas sérialisable JSON → l'INSERT lève, mais le `try/except` l'avale. Le test `test_log_event_never_raises` valide ce contrat.

- [ ] **Step 4 : Lancer le test, vérifier le succès**

Run: `cd core/src && DEBUG=True SECRET_KEY=test ../../venv/Scripts/python.exe manage.py test app.tests.LogEventTests -v 2`
Expected: PASS (2 tests).

- [ ] **Step 5 : Commit**

```bash
git add core/src/app/activity.py core/src/app/tests.py
git commit -m "Back-office : helper log_event + récepteurs de signaux auth"
```

---

## Task 3 : Connecter les signaux dans `apps.ready()`

**Files:**
- Modify: `core/src/app/apps.py`
- Test: `core/src/app/tests.py`

- [ ] **Step 1 : Écrire le test qui échoue**

```python
class LoginSignalTests(TestCase):
    def test_login_creates_event(self):
        from django.contrib.auth.models import User
        from .models import ActivityEvent
        User.objects.create_user('jo', password='motdepasse123')
        self.client.login(username='jo', password='motdepasse123')
        self.assertTrue(ActivityEvent.objects.filter(event_type='user_login').exists())
```

- [ ] **Step 2 : Lancer le test, vérifier l'échec**

Run: `cd core/src && DEBUG=True SECRET_KEY=test ../../venv/Scripts/python.exe manage.py test app.tests.LoginSignalTests -v 2`
Expected: FAIL — aucun événement `user_login` (signaux non chargés).

- [ ] **Step 3 : Charger les signaux au démarrage de l'app**

Remplacer `core/src/app/apps.py` par :

```python
from django.apps import AppConfig


class AppConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'app'

    def ready(self):
        from . import activity  # noqa: F401 — connecte les récepteurs de signaux
```

- [ ] **Step 4 : Lancer le test, vérifier le succès**

Run: `cd core/src && DEBUG=True SECRET_KEY=test ../../venv/Scripts/python.exe manage.py test app.tests.LoginSignalTests -v 2`
Expected: PASS.

- [ ] **Step 5 : Commit**

```bash
git add core/src/app/apps.py core/src/app/tests.py
git commit -m "Back-office : active les signaux de journalisation au démarrage"
```

---

## Task 4 : Instrumenter les vues produit

**Files:**
- Modify: `core/src/app/views.py` (plusieurs vues)
- Modify: `core/src/app/tasks.py`
- Test: `core/src/app/tests.py`

- [ ] **Step 1 : Écrire les tests qui échouent**

```python
class InstrumentationTests(TestCase):
    def _user(self):
        from django.contrib.auth.models import User
        u = User.objects.create_user('cre', email='c@x.co', password='motdepasse123')
        self.client.force_login(u)
        return u

    def test_signup_logs_user_signup(self):
        from .models import ActivityEvent
        self.client.post(reverse('signup'), {
            'username': 'neo', 'email': 'neo@x.co', 'password1': 'motdepasse123'})
        self.assertTrue(ActivityEvent.objects.filter(event_type='user_signup').exists())

    def test_new_form_logs_form_created(self):
        from .models import ActivityEvent
        self._user()
        self.client.post(reverse('new_form'), {'template_key': 'restaurant'})
        self.assertTrue(ActivityEvent.objects.filter(event_type='form_created').exists())

    def test_publish_logs_form_published(self):
        from .models import ActivityEvent, VozaviForm
        u = self._user()
        f = VozaviForm.objects.create(user=u, title='F', status='draft')
        self.client.post(reverse('publish_form', args=[f.pk]))
        self.assertTrue(ActivityEvent.objects.filter(event_type='form_published').exists())

    def test_delete_logs_form_deleted_with_title(self):
        from .models import ActivityEvent, VozaviForm
        u = self._user()
        f = VozaviForm.objects.create(user=u, title='À jeter', slug='x1', status='active')
        self.client.post(reverse('delete_form', args=[f.pk]))
        e = ActivityEvent.objects.get(event_type='form_deleted')
        self.assertEqual(e.label, 'À jeter')          # titre conservé après suppression

    def test_public_submission_logs_response_received(self):
        from .models import ActivityEvent, VozaviForm, Question
        from django.test import override_settings
        u = self._user(); self.client.logout()
        f = VozaviForm.objects.create(user=u, title='F', slug='pub1', status='active')
        q = Question.objects.create(form=f, type='text', label='Avis', required=False,
                                    position=0, options={})
        with override_settings(CACHES={'default': {'BACKEND':
                'django.core.cache.backends.locmem.LocMemCache'}}):
            self.client.post(reverse('public_form', args=['pub1']), {f'q_{q.pk}': 'Top'})
        self.assertTrue(ActivityEvent.objects.filter(event_type='response_received').exists())
```

- [ ] **Step 2 : Lancer, vérifier l'échec**

Run: `cd core/src && DEBUG=True SECRET_KEY=test ../../venv/Scripts/python.exe manage.py test app.tests.InstrumentationTests -v 2`
Expected: FAIL (aucun événement journalisé).

- [ ] **Step 3 : Ajouter les appels `log_event`**

En haut de `core/src/app/views.py`, après les imports existants, ajouter :

```python
from .activity import log_event
```

Puis insérer les appels (les ancres ci-dessous existent déjà dans le fichier) :

**a) `signup_view`** — après `login(request, user)` (création de compte), avant le bloc `if claim_pk:` :
```python
            log_event('user_signup', actor=user, request=request, label=user.get_username())
```
Et dans le bloc claim, juste avant `return redirect('share_form', pk=anon_form.pk)` :
```python
                    log_event('guest_form_claimed', actor=user, target=anon_form, request=request)
```

**b) `new_form`** — après `Question.objects.bulk_create([...])` et avant le `if user is None:` :
```python
        log_event('form_created', actor=user, target=vform, request=request)
```

**c) `publish_form`** — après `vform.save()` (statut actif), avant `return redirect('share_form', ...)` :
```python
        log_event('form_published', actor=request.user, target=vform, request=request)
```

**d) `toggle_form_status`** — dans la branche `if vform.status == 'active':` après `vform.save()` :
```python
        log_event('form_closed', actor=request.user, target=vform, request=request)
```
dans la branche `elif vform.status == 'closed':` après `vform.save()` :
```python
        log_event('form_reopened', actor=request.user, target=vform, request=request)
```

**e) `duplicate_form`** — après `Question.objects.bulk_create([...])`, avant `return redirect('edit_form', pk=copy.pk)` :
```python
    log_event('form_duplicated', actor=request.user, target=copy, request=request,
              source_id=original.pk)
```

**f) `delete_form`** — remplacer le bloc POST :
```python
    if request.method == 'POST':
        cache.delete(f'form_results_{vform.pk}')
        title = vform.title
        nb = vform.responses.count()
        vform.delete()
        log_event('form_deleted', actor=request.user, label=title, request=request,
                  responses=nb)
        return redirect('forms_list')
```

**g) `public_form`** — dans `if not errors:`, après `cache.delete(f'form_results_{vform.pk}')` :
```python
            log_event('response_received', actor=vform.user, target=vform, request=request)
```

**h) `contact_view`** — après `ContactMessage.objects.create(...)` :
```python
            log_event('contact_message', request=request, label=name, category=category)
```

**i) `delete_account`** — remplacer la suppression réussie :
```python
        if user.check_password(request.POST.get('password', '')):
            username = user.get_username()
            logout(request)
            user.delete()
            log_event('account_deleted', label=username)
            return redirect('home')
```

- [ ] **Step 4 : Instrumenter la tâche e-mail**

Dans `core/src/app/tasks.py`, fonction `send_new_response_email`, remplacer le bloc `try/except` d'envoi :
```python
    try:
        send_mail(subject, text, settings.DEFAULT_FROM_EMAIL,
                  [vform.user.email], html_message=html, fail_silently=False)
        from .activity import log_event
        log_event('email_sent', actor=vform.user, target=vform, label=vform.title)
    except Exception as e:
        logger.error(f"Échec notification nouvelle réponse (form {form_id}): {e}")
        from .activity import log_event
        log_event('email_failed', actor=vform.user, target=vform, label=vform.title,
                  success=False, error=str(e)[:200])
```

- [ ] **Step 5 : Lancer, vérifier le succès**

Run: `cd core/src && DEBUG=True SECRET_KEY=test ../../venv/Scripts/python.exe manage.py test app.tests.InstrumentationTests -v 2`
Expected: PASS (5 tests).

- [ ] **Step 6 : Non-régression complète de `app`**

Run: `cd core/src && DEBUG=True SECRET_KEY=test ../../venv/Scripts/python.exe manage.py test app -v 1`
Expected: tous les tests `app` au vert.

- [ ] **Step 7 : Commit**

```bash
git add core/src/app/views.py core/src/app/tasks.py core/src/app/tests.py
git commit -m "Back-office : instrumente les vues produit + e-mails (log_event)"
```

---

## Task 5 : Scaffold de l'app `backoffice` + accès + câblage

**Files:**
- Create: `core/src/backoffice/__init__.py`, `apps.py`, `decorators.py`, `urls.py`, `views.py`, `tests.py`
- Modify: `core/src/core/settings.py`, `core/src/core/urls.py`

- [ ] **Step 1 : Écrire le test d'accès qui échoue**

`core/src/backoffice/tests.py` :
```python
from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User


class AccessControlTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create_superuser('boss', 'boss@x.co', 'motdepasse123')
        self.normal = User.objects.create_user('jo', password='motdepasse123')

    def test_anonymous_redirected(self):
        r = self.client.get(reverse('bo_overview'))
        self.assertEqual(r.status_code, 302)        # vers la connexion

    def test_normal_user_gets_404(self):
        self.client.force_login(self.normal)
        r = self.client.get(reverse('bo_overview'))
        self.assertEqual(r.status_code, 404)        # on ne révèle pas l'existence

    def test_superuser_ok(self):
        self.client.force_login(self.admin)
        r = self.client.get(reverse('bo_overview'))
        self.assertEqual(r.status_code, 200)
```

- [ ] **Step 2 : Créer les fichiers de l'app**

`core/src/backoffice/__init__.py` : (vide)

`core/src/backoffice/apps.py` :
```python
from django.apps import AppConfig


class BackofficeConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'backoffice'
```

`core/src/backoffice/decorators.py` :
```python
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
```

`core/src/backoffice/views.py` :
```python
from django.shortcuts import render
from .decorators import superuser_required


@superuser_required
def overview(request):
    return render(request, 'backoffice/overview.html', {})
```

`core/src/backoffice/urls.py` :
```python
from django.urls import path
from . import views

urlpatterns = [
    path('', views.overview, name='bo_overview'),
]
```

- [ ] **Step 3 : Créer un template minimal**

`core/src/backoffice/templates/backoffice/overview.html` :
```html
<!DOCTYPE html><html lang="fr"><head><meta charset="UTF-8"><title>Admin Vozavi</title></head>
<body><h1>Vue d'ensemble</h1></body></html>
```

- [ ] **Step 4 : Câbler l'app**

Dans `core/src/core/settings.py`, modifier `LOCAL_APPS` :
```python
LOCAL_APPS = [
    'app',
    'backoffice',
]
```

Dans `core/src/core/urls.py`, ajouter dans `urlpatterns` (avant `path('', include('app.urls'))`) :
```python
    path('admin-vozavi/', include('backoffice.urls')),
```

- [ ] **Step 5 : Lancer, vérifier le succès**

Run: `cd core/src && DEBUG=True SECRET_KEY=test ../../venv/Scripts/python.exe manage.py test backoffice.tests.AccessControlTests -v 2`
Expected: PASS (3 tests).

- [ ] **Step 6 : Commit**

```bash
git add core/src/backoffice/ core/src/core/settings.py core/src/core/urls.py
git commit -m "Back-office : app backoffice + contrôle d'accès super-utilisateur"
```

---

## Task 6 : Calculs KPI / funnel / tendances (`kpis.py`)

**Files:**
- Create: `core/src/backoffice/kpis.py`
- Test: `core/src/backoffice/tests.py`

- [ ] **Step 1 : Écrire le test qui échoue**

Ajouter à `core/src/backoffice/tests.py` :
```python
class KpiTests(TestCase):
    def test_funnel_and_counts(self):
        from backoffice.kpis import overview_context
        from app.models import VozaviForm, VozaviResponse
        u1 = User.objects.create_user('a', password='x12345678')
        u2 = User.objects.create_user('b', password='x12345678')
        User.objects.create_user('c', password='x12345678')        # inscrit, sans formulaire
        User.objects.create_superuser('boss', 'b@x.co', 'x12345678')  # exclu des stats
        f1 = VozaviForm.objects.create(user=u1, title='F1', slug='s1', status='active')
        VozaviForm.objects.create(user=u2, title='F2', status='draft')  # créé, non publié
        VozaviResponse.objects.create(form=f1)

        ctx = overview_context()
        self.assertEqual(ctx['users_total'], 3)        # superadmin exclu
        self.assertEqual(ctx['funnel']['signed_up'], 3)
        self.assertEqual(ctx['funnel']['created'], 2)  # u1, u2
        self.assertEqual(ctx['funnel']['published'], 1)  # u1
        self.assertEqual(ctx['funnel']['with_response'], 1)  # u1
        self.assertEqual(ctx['forms_total'], 2)
        self.assertEqual(ctx['responses_total'], 1)
        self.assertEqual(len(ctx['signups_series']), 30)
```

- [ ] **Step 2 : Lancer, vérifier l'échec**

Run: `cd core/src && DEBUG=True SECRET_KEY=test ../../venv/Scripts/python.exe manage.py test backoffice.tests.KpiTests -v 2`
Expected: FAIL — `ModuleNotFoundError: No module named 'backoffice.kpis'`.

- [ ] **Step 3 : Implémenter `kpis.py`**

`core/src/backoffice/kpis.py` :
```python
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
```

- [ ] **Step 4 : Lancer, vérifier le succès**

Run: `cd core/src && DEBUG=True SECRET_KEY=test ../../venv/Scripts/python.exe manage.py test backoffice.tests.KpiTests -v 2`
Expected: PASS.

- [ ] **Step 5 : Commit**

```bash
git add core/src/backoffice/kpis.py core/src/backoffice/tests.py
git commit -m "Back-office : calculs KPI / funnel / tendances"
```

---

## Task 7 : Chrome `base_admin.html`

**Files:**
- Create: `core/src/backoffice/templates/backoffice/base_admin.html`

- [ ] **Step 1 : Créer la chrome partagée**

`core/src/backoffice/templates/backoffice/base_admin.html` :
```html
{% load static %}
<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<meta name="robots" content="noindex,nofollow">
<title>{% block title %}Admin Vozavi{% endblock %}</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="preload" as="style" href="https://fonts.googleapis.com/css2?family=Poppins:wght@400;500;600;700;800&family=Inter:wght@400;500;600&display=swap" onload="this.onload=null;this.rel='stylesheet'">
<noscript><link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Poppins:wght@400;500;600;700;800&family=Inter:wght@400;500;600&display=swap"></noscript>
<link rel="stylesheet" href="{% static 'app/css/vozavi.css' %}">
<script src="https://cdn.jsdelivr.net/npm/htmx.org@1.9.12/dist/htmx.min.js" crossorigin="anonymous" defer></script>
<style>
.bo{display:grid;grid-template-columns:230px 1fr;min-height:100dvh}
.bo-side{background:#1A1929;padding:22px 14px;display:flex;flex-direction:column;gap:4px}
.bo-brand{font-family:var(--fh);font-weight:700;color:#fff;font-size:1.05rem;padding:8px 12px 18px}
.bo-brand span{color:var(--amb)}
.bo-link{display:flex;align-items:center;gap:10px;padding:10px 12px;border-radius:var(--r-xs);color:rgba(255,255,255,.72);font-family:var(--fh);font-size:.875rem;font-weight:500;transition:background .14s,color .14s}
.bo-link:hover{background:rgba(255,255,255,.07);color:#fff}
.bo-link.active{background:var(--ind);color:#fff}
.bo-main{padding:28px clamp(18px,3vw,40px);max-width:1180px}
.bo-h1{font-family:var(--fh);font-weight:700;font-size:1.5rem;color:var(--txt);margin-bottom:22px}
.bo-cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:14px}
.bo-card{background:var(--white);border:1px solid var(--bdr);border-radius:var(--r);padding:18px;box-shadow:var(--sh)}
.bo-card-k{font-family:var(--fh);font-size:1.9rem;font-weight:700;color:var(--ind);line-height:1}
.bo-card-l{font-size:.8rem;color:var(--txt-3);margin-top:6px;font-family:var(--fh)}
.bo-section{background:var(--white);border:1px solid var(--bdr);border-radius:var(--r);padding:20px;box-shadow:var(--sh);margin-top:20px}
.bo-section h2{font-family:var(--fh);font-size:1.05rem;font-weight:700;margin-bottom:14px}
.bo-table{width:100%;border-collapse:collapse;font-size:.85rem}
.bo-table th{text-align:left;color:var(--txt-3);font-family:var(--fh);font-weight:600;padding:8px 10px;border-bottom:1px solid var(--bdr)}
.bo-table td{padding:9px 10px;border-bottom:1px solid var(--bdr)}
.bo-badge{display:inline-block;padding:2px 9px;border-radius:var(--r-pill,999px);font-size:.72rem;font-weight:600;font-family:var(--fh)}
.bo-ok{background:var(--grn-pale);color:var(--grn)}
.bo-ko{background:var(--red-pale);color:var(--red)}
.bo-bar{height:8px;background:var(--ind);border-radius:4px;min-width:2px}
@media(max-width:760px){.bo{grid-template-columns:1fr}.bo-side{flex-direction:row;flex-wrap:wrap;min-height:auto}}
</style>
{% block extra_css %}{% endblock %}
</head>
<body>
<div class="bo">
  <aside class="bo-side">
    <div class="bo-brand">vozavi<span>·admin</span></div>
    <a href="{% url 'bo_overview' %}" class="bo-link {% if active == 'overview' %}active{% endif %}">Vue d'ensemble</a>
    <a href="{% url 'bo_users' %}" class="bo-link {% if active == 'users' %}active{% endif %}">Utilisateurs</a>
    <a href="{% url 'bo_journal' %}" class="bo-link {% if active == 'journal' %}active{% endif %}">Journal</a>
    <a href="{% url 'bo_health' %}" class="bo-link {% if active == 'health' %}active{% endif %}">Santé technique</a>
    <a href="{% url 'dashboard' %}" class="bo-link" style="margin-top:auto">← Retour à l'app</a>
  </aside>
  <main class="bo-main">
    <h1 class="bo-h1">{% block heading %}{% endblock %}</h1>
    {% block content %}{% endblock %}
  </main>
</div>
{% block extra_js %}{% endblock %}
</body>
</html>
```

- [ ] **Step 2 : Commit**

```bash
git add core/src/backoffice/templates/backoffice/base_admin.html
git commit -m "Back-office : chrome base_admin (barre latérale + tokens vozavi)"
```

Note : les vues des tâches suivantes définissent `active`, `bo_users`, `bo_journal`, `bo_health` — créés en Tasks 8/10/11/12. Ne pas exécuter de rendu avant la Task 8 qui pose toutes les routes.

---

## Task 8 : Vue d'ensemble (overview) + fragment KPI (polling)

**Files:**
- Modify: `core/src/backoffice/views.py`, `core/src/backoffice/urls.py`
- Create: `core/src/backoffice/templates/backoffice/overview.html`, `core/src/backoffice/templates/backoffice/partials/kpis.html`
- Test: `core/src/backoffice/tests.py`

- [ ] **Step 1 : Écrire le test qui échoue**

```python
class OverviewRenderTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create_superuser('boss', 'b@x.co', 'x12345678')
        self.client.force_login(self.admin)

    def test_overview_shows_kpis(self):
        from app.models import VozaviForm
        User.objects.create_user('a', password='x12345678')
        VozaviForm.objects.create(title='F', status='active', slug='s1')
        r = self.client.get(reverse('bo_overview'))
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, 'Utilisateurs')
        self.assertContains(r, 'Funnel')

    def test_kpis_partial_ok(self):
        r = self.client.get(reverse('bo_kpis_partial'))
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, 'bo-card')
```

- [ ] **Step 2 : Lancer, vérifier l'échec**

Run: `cd core/src && DEBUG=True SECRET_KEY=test ../../venv/Scripts/python.exe manage.py test backoffice.tests.OverviewRenderTests -v 2`
Expected: FAIL — `NoReverseMatch: 'bo_kpis_partial'`.

- [ ] **Step 3 : Vues**

Remplacer `core/src/backoffice/views.py` par :
```python
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
```

- [ ] **Step 4 : Routes**

`core/src/backoffice/urls.py` :
```python
from django.urls import path
from . import views

urlpatterns = [
    path('', views.overview, name='bo_overview'),
    path('partials/kpis/', views.kpis_partial, name='bo_kpis_partial'),
]
```

- [ ] **Step 5 : Templates**

`core/src/backoffice/templates/backoffice/partials/kpis.html` :
```html
<div class="bo-cards">
  <div class="bo-card"><div class="bo-card-k">{{ users_total }}</div><div class="bo-card-l">Utilisateurs</div></div>
  <div class="bo-card"><div class="bo-card-k">{{ users_active_7d }}</div><div class="bo-card-l">Actifs 7 j</div></div>
  <div class="bo-card"><div class="bo-card-k">{{ forms_total }}</div><div class="bo-card-l">Formulaires</div></div>
  <div class="bo-card"><div class="bo-card-k">{{ forms_active }}</div><div class="bo-card-l">Actifs</div></div>
  <div class="bo-card"><div class="bo-card-k">{{ responses_total }}</div><div class="bo-card-l">Réponses</div></div>
  <div class="bo-card"><div class="bo-card-k">{{ publish_rate }} %</div><div class="bo-card-l">Taux de publication</div></div>
  <div class="bo-card"><div class="bo-card-k">{{ avg_responses }}</div><div class="bo-card-l">Réponses / formulaire</div></div>
</div>
```

`core/src/backoffice/templates/backoffice/overview.html` :
```html
{% extends 'backoffice/base_admin.html' %}
{% block title %}Vue d'ensemble — Admin Vozavi{% endblock %}
{% block heading %}Vue d'ensemble{% endblock %}
{% block content %}
<div hx-get="{% url 'bo_kpis_partial' %}" hx-trigger="every 20s" hx-swap="innerHTML">
  {% include 'backoffice/partials/kpis.html' %}
</div>

<div class="bo-section">
  <h2>Funnel d'activation</h2>
  <table class="bo-table">
    <tr><td>Inscrits</td><td><strong>{{ funnel.signed_up }}</strong></td></tr>
    <tr><td>Ont créé un formulaire</td><td><strong>{{ funnel.created }}</strong></td></tr>
    <tr><td>Ont publié</td><td><strong>{{ funnel.published }}</strong></td></tr>
    <tr><td>Ont ≥ 1 réponse</td><td><strong>{{ funnel.with_response }}</strong></td></tr>
  </table>
</div>

<div class="bo-section">
  <h2>Inscriptions (30 j)</h2>
  <table class="bo-table">
    {% for d in signups_series %}
    <tr><td style="width:60px">{{ d.label }}</td>
      <td><div class="bo-bar" style="width:{{ d.pct }}%"></div></td>
      <td style="width:40px;text-align:right">{{ d.count }}</td></tr>
    {% endfor %}
  </table>
</div>

<div class="bo-section">
  <h2>Réponses (30 j)</h2>
  <table class="bo-table">
    {% for d in responses_series %}
    <tr><td style="width:60px">{{ d.label }}</td>
      <td><div class="bo-bar" style="width:{{ d.pct }}%"></div></td>
      <td style="width:40px;text-align:right">{{ d.count }}</td></tr>
    {% endfor %}
  </table>
</div>
{% endblock %}
```

- [ ] **Step 6 : Lancer, vérifier le succès**

Run: `cd core/src && DEBUG=True SECRET_KEY=test ../../venv/Scripts/python.exe manage.py test backoffice.tests.OverviewRenderTests -v 2`
Expected: PASS.

- [ ] **Step 7 : Commit**

```bash
git add core/src/backoffice/
git commit -m "Back-office : vue d'ensemble (KPI + funnel + tendances) + polling"
```

---

## Task 9 : Liste des utilisateurs

**Files:**
- Modify: `core/src/backoffice/views.py`, `core/src/backoffice/urls.py`
- Create: `core/src/backoffice/templates/backoffice/users.html`
- Test: `core/src/backoffice/tests.py`

- [ ] **Step 1 : Écrire le test qui échoue**

```python
class UsersListTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create_superuser('boss', 'b@x.co', 'x12345678')
        self.client.force_login(self.admin)

    def test_list_shows_users_and_search(self):
        from app.models import VozaviForm
        u = User.objects.create_user('awa', email='awa@x.co', password='x12345678')
        VozaviForm.objects.create(user=u, title='F', status='active', slug='s1')
        r = self.client.get(reverse('bo_users'))
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, 'awa@x.co')
        r2 = self.client.get(reverse('bo_users'), {'q': 'introuvable'})
        self.assertNotContains(r2, 'awa@x.co')
```

- [ ] **Step 2 : Lancer, vérifier l'échec**

Run: `cd core/src && DEBUG=True SECRET_KEY=test ../../venv/Scripts/python.exe manage.py test backoffice.tests.UsersListTests -v 2`
Expected: FAIL — `NoReverseMatch: 'bo_users'`.

- [ ] **Step 3 : Vue (ajouter à `views.py`)**

```python
from django.contrib.auth.models import User
from django.core.paginator import Paginator
from django.db.models import Count, Max, Q


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
```

- [ ] **Step 4 : Route (ajouter à `urls.py`)**

```python
    path('users/', views.users_list, name='bo_users'),
```

- [ ] **Step 5 : Template**

`core/src/backoffice/templates/backoffice/users.html` :
```html
{% extends 'backoffice/base_admin.html' %}
{% block title %}Utilisateurs — Admin Vozavi{% endblock %}
{% block heading %}Utilisateurs{% endblock %}
{% block content %}
<form method="get" style="margin-bottom:16px">
  <input type="search" name="q" value="{{ q }}" placeholder="Rechercher (nom, e-mail)…"
         style="padding:10px 14px;border:1.5px solid var(--bdr);border-radius:var(--r-sm);width:min(360px,100%);font-family:var(--fb)">
</form>
<div class="bo-section" style="padding:0;overflow:auto">
  <table class="bo-table">
    <thead><tr><th>Utilisateur</th><th>Inscrit</th><th>Formulaires</th><th>Réponses</th><th>Dernière activité</th><th>Statut</th></tr></thead>
    <tbody>
    {% for u in page_obj %}
      <tr>
        <td><a href="{% url 'bo_user_detail' u.pk %}" style="color:var(--ind);font-weight:600">{{ u.email|default:u.username }}</a></td>
        <td>{{ u.date_joined|date:'d/m/Y' }}</td>
        <td>{{ u.nb_forms }}</td>
        <td>{{ u.nb_responses }}</td>
        <td>{{ u.last_login|default:u.date_joined|date:'d/m/Y H:i' }}</td>
        <td>{% if u.is_active %}<span class="bo-badge bo-ok">Actif</span>{% else %}<span class="bo-badge bo-ko">Désactivé</span>{% endif %}</td>
      </tr>
    {% empty %}
      <tr><td colspan="6" style="text-align:center;color:var(--txt-3);padding:24px">Aucun utilisateur.</td></tr>
    {% endfor %}
    </tbody>
  </table>
</div>
{% if page_obj.has_other_pages %}
<div style="margin-top:14px;display:flex;gap:10px">
  {% if page_obj.has_previous %}<a class="bo-link" style="color:var(--ind)" href="?q={{ q }}&page={{ page_obj.previous_page_number }}">← Préc.</a>{% endif %}
  <span style="color:var(--txt-3)">Page {{ page_obj.number }}/{{ page_obj.paginator.num_pages }}</span>
  {% if page_obj.has_next %}<a class="bo-link" style="color:var(--ind)" href="?q={{ q }}&page={{ page_obj.next_page_number }}">Suiv. →</a>{% endif %}
</div>
{% endif %}
{% endblock %}
```

- [ ] **Step 6 : Lancer, vérifier le succès**

Run: `cd core/src && DEBUG=True SECRET_KEY=test ../../venv/Scripts/python.exe manage.py test backoffice.tests.UsersListTests -v 2`
Expected: PASS.

- [ ] **Step 7 : Commit**

```bash
git add core/src/backoffice/
git commit -m "Back-office : liste des utilisateurs (recherche, pagination)"
```

---

## Task 10 : Fiche utilisateur + actions (désactiver / supprimer)

**Files:**
- Modify: `core/src/backoffice/views.py`, `core/src/backoffice/urls.py`
- Create: `core/src/backoffice/templates/backoffice/user_detail.html`
- Test: `core/src/backoffice/tests.py`

- [ ] **Step 1 : Écrire les tests qui échouent**

```python
class UserActionsTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create_superuser('boss', 'b@x.co', 'x12345678')
        self.admin2 = User.objects.create_superuser('boss2', 'b2@x.co', 'x12345678')
        self.target = User.objects.create_user('cible', password='x12345678')
        self.client.force_login(self.admin)

    def test_detail_renders(self):
        r = self.client.get(reverse('bo_user_detail', args=[self.target.pk]))
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, 'cible')

    def test_deactivate_sets_inactive_and_logs(self):
        from app.models import ActivityEvent
        self.client.post(reverse('bo_user_toggle', args=[self.target.pk]))
        self.target.refresh_from_db()
        self.assertFalse(self.target.is_active)
        self.assertTrue(ActivityEvent.objects.filter(event_type='account_deactivated').exists())

    def test_cannot_deactivate_self(self):
        self.client.post(reverse('bo_user_toggle', args=[self.admin.pk]))
        self.admin.refresh_from_db()
        self.assertTrue(self.admin.is_active)        # inchangé

    def test_cannot_deactivate_other_superuser(self):
        self.client.post(reverse('bo_user_toggle', args=[self.admin2.pk]))
        self.admin2.refresh_from_db()
        self.assertTrue(self.admin2.is_active)

    def test_delete_removes_user_and_logs(self):
        from app.models import ActivityEvent
        pk = self.target.pk
        self.client.post(reverse('bo_user_delete', args=[pk]))
        self.assertFalse(User.objects.filter(pk=pk).exists())
        self.assertTrue(ActivityEvent.objects.filter(event_type='account_deleted_by_admin').exists())

    def test_cannot_delete_other_superuser(self):
        self.client.post(reverse('bo_user_delete', args=[self.admin2.pk]))
        self.assertTrue(User.objects.filter(pk=self.admin2.pk).exists())
```

- [ ] **Step 2 : Lancer, vérifier l'échec**

Run: `cd core/src && DEBUG=True SECRET_KEY=test ../../venv/Scripts/python.exe manage.py test backoffice.tests.UserActionsTests -v 2`
Expected: FAIL — `NoReverseMatch: 'bo_user_detail'`.

- [ ] **Step 3 : Vues (ajouter à `views.py`)**

```python
from django.shortcuts import get_object_or_404, redirect
from django.http import HttpResponse
from app.models import ActivityEvent
from app.activity import log_event


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
```

Note : la réactivation réutilise `user_login` comme trace neutre (pas de type dédié « réactivation » pour rester sur la liste fermée d'événements). Le champ `metadata.now_active` distingue les deux cas.

- [ ] **Step 4 : Routes (ajouter à `urls.py`)**

```python
    path('users/<int:pk>/', views.user_detail, name='bo_user_detail'),
    path('users/<int:pk>/toggle-active/', views.user_toggle_active, name='bo_user_toggle'),
    path('users/<int:pk>/delete/', views.user_delete, name='bo_user_delete'),
```

- [ ] **Step 5 : Template**

`core/src/backoffice/templates/backoffice/user_detail.html` :
```html
{% extends 'backoffice/base_admin.html' %}
{% block title %}{{ target.email|default:target.username }} — Admin Vozavi{% endblock %}
{% block heading %}{{ target.email|default:target.username }}{% endblock %}
{% block content %}
<p style="margin-bottom:16px">
  Inscrit le {{ target.date_joined|date:'d/m/Y' }} ·
  {% if target.is_active %}<span class="bo-badge bo-ok">Actif</span>{% else %}<span class="bo-badge bo-ko">Désactivé</span>{% endif %}
</p>

{% if confirm_delete %}
<div class="bo-section" style="border-color:var(--red)">
  <h2>Supprimer définitivement ce compte&nbsp;?</h2>
  <p style="color:var(--txt-2);margin-bottom:14px">Cette action supprime le compte et tous ses formulaires et réponses. Irréversible.</p>
  <form method="post" action="{% url 'bo_user_delete' target.pk %}">{% csrf_token %}
    <button class="bo-badge bo-ko" style="border:none;cursor:pointer;padding:10px 18px">Confirmer la suppression</button>
    <a href="{% url 'bo_user_detail' target.pk %}" style="margin-left:12px">Annuler</a>
  </form>
</div>
{% endif %}

{% if not protected %}
<div class="bo-section">
  <h2>Actions</h2>
  <form method="post" action="{% url 'bo_user_toggle' target.pk %}" style="display:inline">{% csrf_token %}
    <button style="padding:9px 16px;border:1.5px solid var(--bdr);border-radius:var(--r-sm);background:#fff;cursor:pointer;font-family:var(--fh)">
      {% if target.is_active %}Désactiver le compte{% else %}Réactiver le compte{% endif %}
    </button>
  </form>
  <a href="{% url 'bo_user_delete' target.pk %}" style="margin-left:10px;padding:9px 16px;border:1.5px solid var(--red);color:var(--red);border-radius:var(--r-sm);font-family:var(--fh)">Supprimer…</a>
</div>
{% else %}
<p style="color:var(--txt-3)">Compte protégé (vous-même ou un autre administrateur) — actions désactivées.</p>
{% endif %}

<div class="bo-section" style="padding:0;overflow:auto">
  <h2 style="padding:18px 18px 0">Formulaires</h2>
  <table class="bo-table">
    <thead><tr><th>Titre</th><th>Statut</th><th>Réponses</th></tr></thead>
    <tbody>
    {% for f in forms %}
      <tr><td>{{ f.title }}</td><td>{{ f.get_status_display }}</td><td>{{ f.nb }}</td></tr>
    {% empty %}<tr><td colspan="3" style="padding:18px;color:var(--txt-3)">Aucun formulaire.</td></tr>{% endfor %}
    </tbody>
  </table>
</div>

<div class="bo-section">
  <h2>Activité récente</h2>
  <table class="bo-table">
    {% for e in events %}
    <tr><td style="width:130px;color:var(--txt-3)">{{ e.created_at|date:'d/m H:i' }}</td>
      <td>{{ e.get_event_type_display }}</td>
      <td>{{ e.label }}</td></tr>
    {% empty %}<tr><td style="color:var(--txt-3);padding:14px">Aucun événement.</td></tr>{% endfor %}
  </table>
</div>
{% endblock %}
```

- [ ] **Step 6 : Lancer, vérifier le succès**

Run: `cd core/src && DEBUG=True SECRET_KEY=test ../../venv/Scripts/python.exe manage.py test backoffice.tests.UserActionsTests -v 2`
Expected: PASS (6 tests).

- [ ] **Step 7 : Commit**

```bash
git add core/src/backoffice/
git commit -m "Back-office : fiche utilisateur + actions (désactiver/supprimer) avec garde-fous"
```

---

## Task 11 : Journal d'événements + fragment flux (polling)

**Files:**
- Modify: `core/src/backoffice/views.py`, `core/src/backoffice/urls.py`
- Create: `core/src/backoffice/templates/backoffice/journal.html`, `core/src/backoffice/templates/backoffice/partials/feed.html`
- Test: `core/src/backoffice/tests.py`

- [ ] **Step 1 : Écrire le test qui échoue**

```python
class JournalTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create_superuser('boss', 'b@x.co', 'x12345678')
        self.client.force_login(self.admin)

    def test_journal_lists_and_filters(self):
        from app.models import ActivityEvent
        ActivityEvent.objects.create(event_type='form_published', label='Resto')
        ActivityEvent.objects.create(event_type='response_received', label='NPS')
        r = self.client.get(reverse('bo_journal'))
        self.assertContains(r, 'Resto')
        self.assertContains(r, 'NPS')
        r2 = self.client.get(reverse('bo_journal'), {'type': 'form_published'})
        self.assertContains(r2, 'Resto')
        self.assertNotContains(r2, 'NPS')

    def test_feed_partial_ok(self):
        r = self.client.get(reverse('bo_journal_feed'))
        self.assertEqual(r.status_code, 200)
```

- [ ] **Step 2 : Lancer, vérifier l'échec**

Run: `cd core/src && DEBUG=True SECRET_KEY=test ../../venv/Scripts/python.exe manage.py test backoffice.tests.JournalTests -v 2`
Expected: FAIL — `NoReverseMatch: 'bo_journal'`.

- [ ] **Step 3 : Vues (ajouter à `views.py`)**

`ActivityEvent` est déjà importé dans `views.py` (Task 10). Ajouter seulement :

```python
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
```

- [ ] **Step 4 : Routes (ajouter à `urls.py`)**

```python
    path('journal/', views.journal, name='bo_journal'),
    path('partials/journal-feed/', views.journal_feed, name='bo_journal_feed'),
```

- [ ] **Step 5 : Templates**

`core/src/backoffice/templates/backoffice/partials/feed.html` :
```html
<table class="bo-table">
  <thead><tr><th>Quand</th><th>Type</th><th>Acteur</th><th>Cible</th><th>État</th></tr></thead>
  <tbody>
  {% for e in events %}
    <tr>
      <td style="width:130px;color:var(--txt-3)">{{ e.created_at|date:'d/m H:i:s' }}</td>
      <td>{{ e.get_event_type_display }}</td>
      <td>{% if e.actor %}{{ e.actor.email|default:e.actor.username }}{% else %}—{% endif %}</td>
      <td>{{ e.label }}</td>
      <td>{% if e.success %}<span class="bo-badge bo-ok">OK</span>{% else %}<span class="bo-badge bo-ko">Échec</span>{% endif %}</td>
    </tr>
  {% empty %}
    <tr><td colspan="5" style="text-align:center;color:var(--txt-3);padding:24px">Aucun événement.</td></tr>
  {% endfor %}
  </tbody>
</table>
```

`core/src/backoffice/templates/backoffice/journal.html` :
```html
{% extends 'backoffice/base_admin.html' %}
{% block title %}Journal — Admin Vozavi{% endblock %}
{% block heading %}Journal d'événements{% endblock %}
{% block content %}
<form method="get" style="display:flex;gap:10px;margin-bottom:16px;flex-wrap:wrap">
  <select name="type" onchange="this.form.submit()" style="padding:9px 12px;border:1.5px solid var(--bdr);border-radius:var(--r-sm);font-family:var(--fb)">
    <option value="">Tous les types</option>
    {% for value, lbl in event_types %}
    <option value="{{ value }}" {% if value == type %}selected{% endif %}>{{ lbl }}</option>
    {% endfor %}
  </select>
  <input type="search" name="q" value="{{ q }}" placeholder="Acteur ou cible…"
         style="padding:9px 12px;border:1.5px solid var(--bdr);border-radius:var(--r-sm);font-family:var(--fb)">
  <button style="padding:9px 16px;border:none;background:var(--ind);color:#fff;border-radius:var(--r-sm);font-family:var(--fh);cursor:pointer">Filtrer</button>
</form>

{% if not type and not q %}
<div class="bo-section" style="padding:0;overflow:auto">
  <h2 style="padding:16px 18px 0">Flux temps réel</h2>
  <div hx-get="{% url 'bo_journal_feed' %}" hx-trigger="every 15s" hx-swap="innerHTML">
    {% include 'backoffice/partials/feed.html' with events=page_obj %}
  </div>
</div>
{% else %}
<div class="bo-section" style="padding:0;overflow:auto">
  {% include 'backoffice/partials/feed.html' with events=page_obj %}
</div>
{% endif %}

{% if page_obj.has_other_pages %}
<div style="margin-top:14px;display:flex;gap:10px">
  {% if page_obj.has_previous %}<a style="color:var(--ind)" href="?type={{ type }}&q={{ q }}&page={{ page_obj.previous_page_number }}">← Préc.</a>{% endif %}
  <span style="color:var(--txt-3)">Page {{ page_obj.number }}/{{ page_obj.paginator.num_pages }}</span>
  {% if page_obj.has_next %}<a style="color:var(--ind)" href="?type={{ type }}&q={{ q }}&page={{ page_obj.next_page_number }}">Suiv. →</a>{% endif %}
</div>
{% endif %}
{% endblock %}
```

- [ ] **Step 6 : Lancer, vérifier le succès**

Run: `cd core/src && DEBUG=True SECRET_KEY=test ../../venv/Scripts/python.exe manage.py test backoffice.tests.JournalTests -v 2`
Expected: PASS.

- [ ] **Step 7 : Commit**

```bash
git add core/src/backoffice/
git commit -m "Back-office : journal d'événements filtrable + flux temps réel"
```

---

## Task 12 : Santé technique

**Files:**
- Modify: `core/src/backoffice/views.py`, `core/src/backoffice/urls.py`
- Create: `core/src/backoffice/templates/backoffice/health.html`
- Test: `core/src/backoffice/tests.py`

- [ ] **Step 1 : Écrire le test qui échoue**

```python
class HealthTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create_superuser('boss', 'b@x.co', 'x12345678')
        self.client.force_login(self.admin)

    def test_health_counts(self):
        from app.models import ActivityEvent, ContactMessage
        ActivityEvent.objects.create(event_type='email_failed', success=False, label='x')
        ContactMessage.objects.create(name='A', email='a@x.co', message='hi')
        r = self.client.get(reverse('bo_health'))
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, 'Contacts non lus')
        self.assertContains(r, 'E-mails échoués')
```

- [ ] **Step 2 : Lancer, vérifier l'échec**

Run: `cd core/src && DEBUG=True SECRET_KEY=test ../../venv/Scripts/python.exe manage.py test backoffice.tests.HealthTests -v 2`
Expected: FAIL — `NoReverseMatch: 'bo_health'`.

- [ ] **Step 3 : Vue (ajouter à `views.py`)**

```python
from datetime import timedelta
from django.utils import timezone
from app.models import ContactMessage, VozaviForm


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
```

- [ ] **Step 4 : Route (ajouter à `urls.py`)**

```python
    path('health/', views.health, name='bo_health'),
```

- [ ] **Step 5 : Template**

`core/src/backoffice/templates/backoffice/health.html` :
```html
{% extends 'backoffice/base_admin.html' %}
{% block title %}Santé technique — Admin Vozavi{% endblock %}
{% block heading %}Santé technique{% endblock %}
{% block content %}
<div class="bo-cards">
  <div class="bo-card"><div class="bo-card-k">{{ emails_sent }}</div><div class="bo-card-l">E-mails envoyés</div></div>
  <div class="bo-card"><div class="bo-card-k">{{ emails_failed }}</div><div class="bo-card-l">E-mails échoués</div></div>
  <div class="bo-card"><div class="bo-card-k">{{ contacts_unread }}</div><div class="bo-card-l">Contacts non lus</div></div>
  <div class="bo-card"><div class="bo-card-k">{{ guest_forms }}</div><div class="bo-card-l">Formulaires invités (&lt;48 h)</div></div>
</div>
<div class="bo-section">
  <h2>Derniers échecs</h2>
  <table class="bo-table">
    <thead><tr><th>Quand</th><th>Type</th><th>Cible</th><th>Détail</th></tr></thead>
    <tbody>
    {% for e in recent_failures %}
      <tr><td style="width:130px;color:var(--txt-3)">{{ e.created_at|date:'d/m H:i' }}</td>
        <td>{{ e.get_event_type_display }}</td><td>{{ e.label }}</td>
        <td style="color:var(--txt-3)">{{ e.metadata.error|default:'' }}</td></tr>
    {% empty %}<tr><td colspan="4" style="text-align:center;color:var(--grn);padding:20px">Aucun échec récent ✓</td></tr>{% endfor %}
    </tbody>
  </table>
</div>
{% endblock %}
```

- [ ] **Step 6 : Lancer, vérifier le succès**

Run: `cd core/src && DEBUG=True SECRET_KEY=test ../../venv/Scripts/python.exe manage.py test backoffice.tests.HealthTests -v 2`
Expected: PASS.

- [ ] **Step 7 : Commit**

```bash
git add core/src/backoffice/
git commit -m "Back-office : page santé technique"
```

---

## Task 13 : Purge de rétention + non-régression finale

**Files:**
- Modify: `core/src/app/tasks.py`
- Test: `core/src/app/tests.py`

- [ ] **Step 1 : Écrire le test qui échoue**

```python
class EventRetentionTests(TestCase):
    def test_old_events_purged(self):
        from app.models import ActivityEvent
        from app.tasks import cleanup_old_events
        old = ActivityEvent.objects.create(event_type='user_login', label='vieux')
        ActivityEvent.objects.filter(pk=old.pk).update(
            created_at=timezone.now() - timedelta(days=200))
        ActivityEvent.objects.create(event_type='user_login', label='récent')
        cleanup_old_events(days=180)
        self.assertEqual(ActivityEvent.objects.count(), 1)
        self.assertTrue(ActivityEvent.objects.filter(label='récent').exists())
```

Ajouter en haut de `tests.py` si absent : `from django.utils import timezone` et `from datetime import timedelta`.

- [ ] **Step 2 : Lancer, vérifier l'échec**

Run: `cd core/src && DEBUG=True SECRET_KEY=test ../../venv/Scripts/python.exe manage.py test app.tests.EventRetentionTests -v 2`
Expected: FAIL — `ImportError: cannot import name 'cleanup_old_events'`.

- [ ] **Step 3 : Ajouter la tâche**

À la fin de `core/src/app/tasks.py` :
```python
@shared_task
def cleanup_old_events(days=180):
    """Purge les ActivityEvent plus vieux que `days` jours."""
    from .models import ActivityEvent
    cutoff = timezone.now() - timedelta(days=days)
    ActivityEvent.objects.filter(created_at__lt=cutoff).delete()
```

- [ ] **Step 4 : Lancer, vérifier le succès**

Run: `cd core/src && DEBUG=True SECRET_KEY=test ../../venv/Scripts/python.exe manage.py test app.tests.EventRetentionTests -v 2`
Expected: PASS.

- [ ] **Step 5 : Non-régression GLOBALE (app + backoffice)**

Run: `cd core/src && DEBUG=True SECRET_KEY=test ../../venv/Scripts/python.exe manage.py test app backoffice -v 1`
Expected: tout au vert.

- [ ] **Step 6 : Vérification manuelle du rendu (super-utilisateur)**

```bash
cd core/src && DEBUG=True SECRET_KEY=test ALLOWED_HOSTS=testserver \
  ../../venv/Scripts/python.exe -c "
import django,os; os.environ.setdefault('DJANGO_SETTINGS_MODULE','core.settings'); django.setup()
from django.test import Client; from django.contrib.auth.models import User
User.objects.create_superuser('boss','b@x.co','x12345678')
c=Client(); c.force_login(User.objects.get(username='boss'))
for u in ['/admin-vozavi/','/admin-vozavi/users/','/admin-vozavi/journal/','/admin-vozavi/health/']:
    print(u, c.get(u).status_code)
"
```
Expected: chaque route renvoie `200`.

- [ ] **Step 7 : Commit**

```bash
git add core/src/app/tasks.py core/src/app/tests.py
git commit -m "Back-office : purge de rétention des événements (180 j)"
```

---

## Self-Review (couverture spec)

- Modèle `ActivityEvent` + référence souple + `success` → Task 1 ✓
- Helper `log_event` ne lève jamais → Task 2 ✓
- Signaux auth (login/logout) → Tasks 2 (récepteurs) + 3 (chargement) ✓
- Instrumentation de tous les types d'événements → Task 4 (+ e-mails) ✓
- App `backoffice` + accès super-utilisateur (404 non-admin) → Task 5 ✓
- KPI / funnel / tendances + cache 10 s → Task 6 ✓
- Chrome + barre latérale (vozavi.css) → Task 7 ✓
- Vue d'ensemble + polling 20 s → Task 8 ✓
- Liste utilisateurs (recherche, pagination) → Task 9 ✓
- Fiche utilisateur + actions + garde-fous (soi/super-admin) → Task 10 ✓
- Journal filtrable + flux polling 15 s → Task 11 ✓
- Santé technique → Task 12 ✓
- Rétention 180 j → Task 13 ✓

Tous les noms de routes (`bo_*`) et de fonctions sont cohérents entre tâches. Aucun placeholder.
