# Architecture — Vozavi

SaaS de collecte de formulaires et d'avis en ligne. L'utilisateur crée un
formulaire (NPS, satisfaction, avis client, infos prospects), le partage via
lien ou QR code, et consulte les résultats en temps réel dans un dashboard.

Cible : Afrique francophone — PME, restaurants, RH, managers terrain. Public
souvent mobile-first, à connexion variable (d'où les replis sans JavaScript).

## Structure

```
core/
├── requirements.txt
├── ARCHITECTURE.md
└── src/
    ├── manage.py
    ├── core/               # Configuration Django (settings, urls, wsgi, asgi)
    ├── app/                # App unique (modèles, vues, admin, tâches, tests)
    │   ├── models.py       # VozaviForm, Question, VozaviResponse, Answer, ContactMessage
    │   ├── views.py        # builder, formulaires publics, résultats, exports, auth
    │   ├── tasks.py        # notification e-mail + nettoyage des formulaires invités
    │   ├── templates_data.py  # modèles de formulaires pré-remplis
    │   └── tests.py        # ~51 tests
    ├── templates/          # Templates HTML
    │   ├── account/        # auth (login, signup, reset password)
    │   ├── vozavi/         # builder, public, account, pages marketing
    │   └── emails/         # e-mails transactionnels
    ├── static/             # JS (htmx, alpine), logos SVG
    ├── static_cdn/         # statiques collectés (collectstatic)
    ├── media_cdn/          # logos uploadés par les utilisateurs
    └── data/               # données de référence
```

## Modules fonctionnels

- **Builder** : création depuis modèles, édition en direct (HTMX), branding
  (couleur, logo), réordonnancement et types de questions variés (note, choix,
  texte, grille, contact). Repli sans JS si HTMX ne se charge pas.
- **Formulaires invités** : création sans compte (clé de session), « réclamés »
  à l'inscription ; nettoyage automatique des formulaires non réclamés > 48 h.
- **Partage** : lien public `/f/<slug>/`, QR code, WhatsApp, images Open Graph
  générées dynamiquement par formulaire.
- **Résultats** : agrégats par type de question, tendance sur 14 jours, alertes
  avis négatifs, exports CSV (streaming) et Excel.
- **Compte** : auth maison (login rate-limité, reset password Django), gestion
  e-mail / mot de passe, suppression de compte (droit à l'effacement).

## Stack technique

- Backend : Django 5.2 (app unique, sans DRF)
- Base de données : MySQL en prod, SQLite en dev
- Frontend : Django Templates + HTMX + Alpine.js, CSS inline (pas de build front)
- Cache : `DatabaseCache` (pas de Redis requis)
- Tâches : `after_response` (notifications post-réponse, thread) + Celery
  (broker SQLAlchemy sur la même DB, pour le nettoyage planifié)
- E-mails : SMTP via Resend
- Serveur : Gunicorn + WhiteNoise (statiques compressés brotli)
