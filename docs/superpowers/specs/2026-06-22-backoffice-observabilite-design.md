# Spec — Back-office d'observabilité (admin Vozavi)

**Date :** 2026-06-22
**Statut :** validé en brainstorming, en attente de relecture
**Branche cible :** à créer depuis `main` (le travail nettoyage/refonte est sur une branche séparée)

## Objectif

Donner au concepteur du SaaS (super-utilisateur) un back-office complet pour
observer en quasi-temps réel le comportement de Vozavi et de ses utilisateurs :
KPI globaux, funnel d'activation, liste et fiches utilisateurs, journal
d'événements (« qui fait quoi, ce qui aboutit ou non »), santé technique, et
actions d'administration sur les comptes (désactiver / supprimer).

## Décisions de cadrage (validées)

1. **Journalisation = vrai journal d'événements** : nouvelle table `ActivityEvent`
   alimentée par instrumentation des actions clés. Pas de rétro-remplissage de
   l'historique : le journal démarre vide et se remplit à partir du déploiement.
2. **Temps réel = polling HTMX** (~15-30 s) sur les fragments KPI et le flux du
   journal. Pas de WebSockets/ASGI.
3. **4 surfaces** : Vue d'ensemble · Utilisateurs (liste + fiche) · Journal · Santé technique.
4. **Actions admin** : désactiver et supprimer un compte, avec garde-fous.
5. **Architecture (approche A)** : modèle d'événement + helper dans `app/` (le cœur
   produit les événements) ; nouvelle app `backoffice/` en lecture qui sert les
   surfaces. Dépendance `backoffice → app`, jamais l'inverse.

## Architecture

```
app/                     # cœur produit (existant)
  models.py              # + ActivityEvent
  activity.py            # + log_event(...) helper, signaux auth
  views.py / tasks.py    # + appels log_event aux points clés
backoffice/              # NOUVELLE app, super-utilisateur uniquement
  decorators.py          # superuser_required
  views.py               # overview, users, user_detail, journal, health, fragments, actions
  urls.py                # routes /admin-vozavi/...
  kpis.py                # calculs KPI / funnel / tendances (isolé, testable)
  templates/backoffice/  # base_admin.html + pages, réutilise vozavi.css
```

### Modèle `ActivityEvent` (app/models.py)

| Champ | Type | Rôle |
|---|---|---|
| `created_at` | DateTimeField(auto_now_add, db_index) | quand |
| `event_type` | CharField(choices, db_index) | type d'événement (liste fermée) |
| `actor` | FK(User, null, `on_delete=SET_NULL`) | qui (null = invité/anonyme/système) |
| `target_type` | CharField(blank) | type de cible souple (ex. `vozaviform`) |
| `target_id` | PositiveIntegerField(null) | id de la cible (pas de FK dure) |
| `label` | CharField(255, blank) | instantané texte (ex. titre du formulaire) |
| `success` | BooleanField(default=True) | « ce qui a abouti ou non » |
| `ip` | GenericIPAddressField(null) | contexte sécurité |
| `metadata` | JSONField(default=dict) | extras |

- `Meta.ordering = ['-created_at']`
- Index composites : `(event_type, created_at)` et `(actor, created_at)`.
- **Référence souple** (target_type/target_id + label) volontaire : supprimer un
  formulaire n'efface pas son historique, et le titre reste lisible via `label`.

### Helper `log_event` (app/activity.py)

```python
def log_event(event_type, *, actor=None, target=None, label='', success=True,
              request=None, **metadata):
    """Enregistre un ActivityEvent. Ne lève jamais : la journalisation ne doit
    jamais casser la requête produit (try/except + logger.exception)."""
```

- Déduit `actor` et `ip` depuis `request` si fournis.
- Déduit `target_type`/`target_id`/`label` depuis l'objet `target`.
- Toute exception est avalée et loguée (jamais propagée).

### Types d'événements & points d'instrumentation

| event_type | success | Lieu |
|---|---|---|
| `user_signup` | True | `signup_view` (après create_user) |
| `user_login` | True | signal `user_logged_in` |
| `user_logout` | True | signal `user_logged_out` |
| `account_deleted` | True | `delete_account` (par l'utilisateur) |
| `guest_form_claimed` | True | `signup_view` (claim) |
| `form_created` | True | `new_form` |
| `form_published` | True | `publish_form` + claim publiant |
| `form_closed` / `form_reopened` | True | `toggle_form_status` |
| `form_duplicated` | True | `duplicate_form` |
| `form_deleted` | True | `delete_form` (titre capturé avant suppression) |
| `response_received` | True | `public_form` (soumission valide) |
| `contact_message` | True | `contact_view` |
| `email_sent` / `email_failed` | True / False | `tasks.send_new_response_email` |
| `account_deactivated` | True | action admin backoffice |
| `account_deleted_by_admin` | True | action admin backoffice |

### Rétention

Purge optionnelle des événements de plus de 180 jours via une tâche Celery
(même mécanisme que le nettoyage des formulaires invités). Non bloquant pour la v1.

## Accès & routes (backoffice)

- Décorateur `@superuser_required` sur toutes les vues : anonyme → redirigé vers
  connexion ; authentifié non-superadmin → **404** (pas de divulgation).
- Routes sous `/admin-vozavi/` (distinct de `/vz-control-panel/`) :
  - `GET /admin-vozavi/` — vue d'ensemble
  - `GET /admin-vozavi/users/` — liste utilisateurs
  - `GET /admin-vozavi/users/<id>/` — fiche utilisateur
  - `POST /admin-vozavi/users/<id>/toggle-active/` — désactiver/réactiver
  - `POST /admin-vozavi/users/<id>/delete/` — supprimer (page de confirmation en GET)
  - `GET /admin-vozavi/journal/` — journal filtrable
  - `GET /admin-vozavi/health/` — santé technique
  - `GET /admin-vozavi/partials/kpis/` — fragment KPI (polling)
  - `GET /admin-vozavi/partials/journal-feed/` — fragment flux (polling)

## Surfaces

### 1. Vue d'ensemble
Cartes KPI : utilisateurs total, actifs 7 j / 30 j (basé sur `User.last_login`,
champ maintenu par Django, immédiatement peuplé), formulaires par statut
(draft/active/closed), réponses total,
taux de publication (active+closed / total), moyenne réponses/formulaire.
Funnel : inscrits → ont créé un formulaire → ont publié → ont ≥1 réponse.
Courbes : inscriptions et réponses sur 30 j (barres SVG/CSS inline, sans librairie).
Calculs isolés dans `backoffice/kpis.py`, cache 10 s.

### 2. Utilisateurs
Liste : recherche (email/username), tri, colonnes inscrit / #formulaires /
#réponses reçues / dernière activité (`last_login`, sinon `date_joined`) /
statut actif. Pagination.
Fiche : ses formulaires (statut, réponses), sa timeline d'événements
(`ActivityEvent` filtré sur `actor`), ses KPIs, boutons d'action.

### 3. Journal
Flux anté-chrono de tous les `ActivityEvent`, filtres par `event_type` et par
acteur (recherche), pagination, succès/échec visibles. Haut du flux auto-refresh.

### 4. Santé technique
E-mails envoyés/échoués (depuis les événements), contacts non lus
(`ContactMessage.is_read=False`), formulaires invités en attente (<48 h,
`user=None`), derniers échecs (`success=False`).

## Actions admin

- **Désactiver** : `is_active=False` (la connexion est déjà bloquée pour ces
  comptes dans `login_view`). Réversible (réactiver). Journalisé.
- **Supprimer** : suppression définitive en cascade. Confirmation en GET, exécution
  en POST. Journalisé (acteur = l'admin, label = username supprimé).
- **Garde-fous** : impossible de cibler soi-même ou un autre super-utilisateur.

## Temps réel

Fragments KPI et haut du journal rafraîchis via `hx-trigger="every 20s"`
(KPI) / `every 15s` (journal). HTMX chargé sur la chrome back-office.

## Tests (~12)

- `log_event` crée l'événement ; sur erreur interne, ne lève pas.
- Accès : anonyme redirigé ; non-superadmin → 404 ; superadmin → 200 sur chaque surface.
- Instrumentation : signup→`user_signup` ; publish→`form_published` ;
  soumission publique→`response_received` ; suppression→`form_deleted` (titre conservé) ;
  échec e-mail→`email_failed` (`success=False`).
- Actions : désactivation pose `is_active=False` + journalise ; refus sur soi-même
  et sur un autre super-admin ; suppression efface user + cascade + journalise.
- KPI/funnel : valeurs correctes sur un petit jeu de données.

## Hors périmètre (v1)

- Rétro-remplissage de l'historique du journal.
- WebSockets/SSE.
- Export CSV du journal (peut venir en v2).
- Graphiques via librairie JS externe.
