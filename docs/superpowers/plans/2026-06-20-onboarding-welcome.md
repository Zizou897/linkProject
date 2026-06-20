# Onboarding — Accueil + premier formulaire guidé — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Après l'inscription, rediriger le nouvel utilisateur vers un écran de bienvenue qui mène directement au choix du modèle de formulaire, sans passer par le dashboard vide.

**Architecture:** Réutilisation de la page de choix de modèle existante (`vozavi/builder/new.html`). `signup_view` redirige une inscription fraîche vers `/new?bienvenue=1`. La vue `new_form` expose un booléen `welcome` au GET, et `new.html` affiche un en-tête de bienvenue conditionnel à la place de l'en-tête standard. Aucune nouvelle route, aucun modèle, aucune migration.

**Tech Stack:** Django 6 (templates, vues fonction), tests `manage.py test`. Lancer les tests avec `DEBUG=True` (SQLite). Commande type : `cd core/src && DEBUG=True ../../venv/Scripts/python.exe manage.py test app`.

---

## Contexte de fichiers

- `core/src/app/views.py` — `signup_view` (redirection finale) et `new_form` (contexte GET).
- `core/src/templates/vozavi/builder/new.html` — en-tête conditionnel + styles.
- `core/src/app/tests.py` — nouvelle classe de tests `OnboardingWelcomeTests`.

Rappels du code existant :
- `signup_view` se termine par `return redirect('dashboard')` (cas inscription fraîche) ; le cas `claim` renvoie déjà `redirect('share_form', pk=...)` plus haut et ne doit PAS changer.
- `reverse` est déjà importé en haut de `views.py` (`from django.urls import reverse`).
- `new_form` (GET) se termine par `return render(request, 'vozavi/builder/new.html')`.
- Dans `new.html`, le bloc à remplacer conditionnellement est :
  ```html
  <main class="page">
    <div class="page-head">
      <h1 class="page-title">Quel type d'avis voulez-vous recueillir ?</h1>
      <p class="page-sub">Choisissez un modèle prérempli ou partez de zéro pour créer votre formulaire.</p>
    </div>
  ```

---

### Task 1 : Rediriger l'inscription fraîche vers l'écran de bienvenue

**Files:**
- Modify: `core/src/app/views.py` (fin de `signup_view`)
- Test: `core/src/app/tests.py`

- [ ] **Step 1 : Écrire le test qui échoue**

Ajouter à la fin de `core/src/app/tests.py` :

```python
class OnboardingWelcomeTests(TestCase):
    """Onboarding : redirection après inscription + en-tête de bienvenue."""

    def test_signup_redirects_to_welcome(self):
        resp = self.client.post(reverse('signup'), {
            'username': 'nouveau',
            'email': 'nouveau@example.com',
            'password1': 'motdepasse123',
        })
        self.assertRedirects(
            resp, reverse('new_form') + '?bienvenue=1',
            fetch_redirect_response=False,
        )
```

- [ ] **Step 2 : Lancer le test pour vérifier qu'il échoue**

Run: `cd core/src && DEBUG=True ../../venv/Scripts/python.exe manage.py test app.tests.OnboardingWelcomeTests.test_signup_redirects_to_welcome -v 2`
Expected: FAIL — la réponse redirige vers `/dashboard/`, pas vers `/new/?bienvenue=1`.

- [ ] **Step 3 : Implémenter la redirection**

Dans `core/src/app/views.py`, dans `signup_view`, remplacer l'unique ligne :

```python
            return redirect('dashboard')
```

par :

```python
            # Onboarding : inscription fraîche → écran de bienvenue (choix du modèle)
            return redirect(reverse('new_form') + '?bienvenue=1')
```

(Ne pas toucher au cas `claim` qui renvoie `redirect('share_form', ...)` plus haut.)

- [ ] **Step 4 : Lancer le test pour vérifier qu'il passe**

Run: `cd core/src && DEBUG=True ../../venv/Scripts/python.exe manage.py test app.tests.OnboardingWelcomeTests.test_signup_redirects_to_welcome -v 2`
Expected: PASS

- [ ] **Step 5 : Commit**

```bash
git add core/src/app/views.py core/src/app/tests.py
git commit -m "Onboarding : redirige l'inscription vers l'écran de bienvenue"
```

---

### Task 2 : En-tête de bienvenue conditionnel sur /new

**Files:**
- Modify: `core/src/app/views.py` (contexte GET de `new_form`)
- Modify: `core/src/templates/vozavi/builder/new.html` (en-tête conditionnel + styles)
- Test: `core/src/app/tests.py`

- [ ] **Step 1 : Écrire les tests qui échouent**

Ajouter dans la classe `OnboardingWelcomeTests` de `core/src/app/tests.py` :

```python
    def test_welcome_hero_shown_with_param(self):
        resp = self.client.get(reverse('new_form') + '?bienvenue=1')
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'Bienvenue sur Vozavi')

    def test_no_welcome_hero_in_normal_visit(self):
        resp = self.client.get(reverse('new_form'))
        self.assertEqual(resp.status_code, 200)
        self.assertNotContains(resp, 'Bienvenue sur Vozavi')
        self.assertContains(resp, "Quel type d'avis")
```

- [ ] **Step 2 : Lancer les tests pour vérifier qu'ils échouent**

Run: `cd core/src && DEBUG=True ../../venv/Scripts/python.exe manage.py test app.tests.OnboardingWelcomeTests -v 2`
Expected: `test_welcome_hero_shown_with_param` FAIL (le hero n'existe pas encore). Les autres passent.

- [ ] **Step 3 : Exposer `welcome` dans la vue `new_form` (GET)**

Dans `core/src/app/views.py`, remplacer la ligne finale de `new_form` :

```python
    return render(request, 'vozavi/builder/new.html')
```

par :

```python
    return render(request, 'vozavi/builder/new.html', {
        'welcome': request.GET.get('bienvenue') == '1',
    })
```

- [ ] **Step 4 : Ajouter l'en-tête de bienvenue conditionnel dans `new.html`**

Dans `core/src/templates/vozavi/builder/new.html`, remplacer le bloc :

```html
<main class="page">
  <div class="page-head">
    <h1 class="page-title">Quel type d'avis voulez-vous recueillir ?</h1>
    <p class="page-sub">Choisissez un modèle prérempli ou partez de zéro pour créer votre formulaire.</p>
  </div>
```

par :

```html
<main class="page">
  {% if welcome %}
  <div class="welcome-hero">
    <h1 class="page-title">Bienvenue sur Vozavi&nbsp;👋</h1>
    <p class="page-sub">Créons votre premier formulaire. Choisissez un point de départ — vous pourrez tout personnaliser ensuite.</p>
    <div class="welcome-steps" aria-hidden="true">
      <span class="welcome-step"><span class="ws-num">1</span> Créez</span>
      <span class="welcome-arrow">→</span>
      <span class="welcome-step"><span class="ws-num">2</span> Partagez</span>
      <span class="welcome-arrow">→</span>
      <span class="welcome-step"><span class="ws-num">3</span> Écoutez</span>
    </div>
  </div>
  {% else %}
  <div class="page-head">
    <h1 class="page-title">Quel type d'avis voulez-vous recueillir ?</h1>
    <p class="page-sub">Choisissez un modèle prérempli ou partez de zéro pour créer votre formulaire.</p>
  </div>
  {% endif %}
```

- [ ] **Step 5 : Ajouter les styles du hero dans `new.html`**

Dans `core/src/templates/vozavi/builder/new.html`, juste avant la balise `</style>`, ajouter :

```css
/* ── ONBOARDING WELCOME ── */
.welcome-hero{margin-bottom:28px}
.welcome-hero .page-title{margin-bottom:8px}
.welcome-steps{display:inline-flex;align-items:center;gap:10px;flex-wrap:wrap;margin-top:16px;padding:10px 16px;background:var(--indigo-pale,#EEEDFB);border:1px solid var(--indigo-mid,#E4E2F8);border-radius:999px}
.welcome-step{display:inline-flex;align-items:center;gap:7px;font-family:var(--f-head,'Poppins',sans-serif);font-weight:600;font-size:.85rem;color:var(--indigo,#4F46B8)}
.ws-num{display:inline-flex;align-items:center;justify-content:center;width:20px;height:20px;border-radius:50%;background:var(--indigo,#4F46B8);color:#fff;font-size:.72rem;font-weight:700}
.welcome-arrow{color:var(--indigo,#4F46B8);opacity:.55;font-weight:700}
@media(max-width:480px){.welcome-steps{gap:7px;padding:9px 12px}.welcome-step{font-size:.8rem}}
```

- [ ] **Step 6 : Lancer les tests pour vérifier qu'ils passent**

Run: `cd core/src && DEBUG=True ../../venv/Scripts/python.exe manage.py test app.tests.OnboardingWelcomeTests -v 2`
Expected: PASS (3 tests).

- [ ] **Step 7 : Commit**

```bash
git add core/src/app/views.py core/src/templates/vozavi/builder/new.html core/src/app/tests.py
git commit -m "Onboarding : en-tête de bienvenue conditionnel sur /new"
```

---

### Task 3 : Non-régression du flux invité (claim) et suite complète

**Files:**
- Test: `core/src/app/tests.py`

- [ ] **Step 1 : Écrire le test de non-régression du claim**

Ajouter dans la classe `OnboardingWelcomeTests` de `core/src/app/tests.py` :

```python
    def test_signup_with_claim_still_redirects_to_share(self):
        # Un formulaire créé en invité, mémorisé en session, doit être
        # « réclamé » à l'inscription → redirection vers le partage, PAS l'accueil.
        guest_form = VozaviForm.objects.create(user=None, title='Invité', status='draft')
        session = self.client.session
        session['guest_form_pk'] = guest_form.pk
        session.save()

        resp = self.client.post(reverse('signup') + '?claim=%d' % guest_form.pk, {
            'username': 'reclameur',
            'email': 'reclameur@example.com',
            'password1': 'motdepasse123',
            'claim': str(guest_form.pk),
        })
        guest_form.refresh_from_db()
        self.assertEqual(guest_form.user.username, 'reclameur')
        self.assertRedirects(
            resp, reverse('share_form', args=[guest_form.pk]),
            fetch_redirect_response=False,
        )
```

- [ ] **Step 2 : Lancer ce test**

Run: `cd core/src && DEBUG=True ../../venv/Scripts/python.exe manage.py test app.tests.OnboardingWelcomeTests.test_signup_with_claim_still_redirects_to_share -v 2`
Expected: PASS (le cas `claim` n'a pas été modifié en Task 1 ; ce test verrouille la non-régression).

- [ ] **Step 3 : Lancer la suite complète**

Run: `cd core/src && DEBUG=True ../../venv/Scripts/python.exe manage.py test app`
Expected: OK, tous les tests au vert (47 existants + 4 nouveaux = 51).

- [ ] **Step 4 : Commit**

```bash
git add core/src/app/tests.py
git commit -m "Onboarding : test de non-régression du flux invité (claim)"
```

---

## Self-Review

- **Couverture spec :** redirection après inscription (Task 1) ✓ ; `welcome` exposé + hero conditionnel (Task 2) ✓ ; absence de hero en visite normale (Task 2) ✓ ; non-régression création/claim (Task 3) ✓ ; pas de nouveau modèle/route/migration (aucune tâche n'en introduit) ✓.
- **Placeholders :** aucun — chaque étape contient le code et la commande exacts.
- **Cohérence des noms :** paramètre `bienvenue=1` et clé de contexte `welcome` utilisés de façon identique entre vue, template et tests ; chaîne « Bienvenue sur Vozavi » identique entre template et tests.
