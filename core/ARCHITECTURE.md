# Architecture — Bediakon Formation

Application web de soumission, sélection et gestion d'offres de formation.

## Structure

```
core/
├── .gitignore
├── requirements.txt
├── .env.example
├── ARCHITECTURE.md
└── src/
    ├── manage.py
    ├── core/               # Configuration Django (settings, urls, wsgi, asgi)
    ├── app/                # App principale (modèles, vues, admin)
    ├── templates/          # Templates HTML
    │   ├── app/
    │   │   ├── base/       # base.html
    │   │   ├── layout/     # pages principales
    │   │   └── includes/   # composants réutilisables
    │   └── emails/         # templates d'emails
    ├── static/             # Fichiers statiques sources
    ├── static_cdn/         # Fichiers statiques collectés (collectstatic)
    ├── media_cdn/          # Fichiers uploadés par les utilisateurs
    └── data/               # Données de référence (fixtures, imports)
```

## Modules fonctionnels

- **Administrateur** : gestion du catalogue de formations, liens sécurisés, tableau de bord
- **Correspondant** : accès via lien sécurisé, sélection et soumission de formations
- **Analytique** : rapports, répartition des choix, export CSV/Excel/PDF
- **Sessions présentiel** : planification, convocations, suivi des présences

## Stack technique

- Backend : Django + Django REST Framework
- Base de données : PostgreSQL (SQLite en dev)
- Frontend : Django Templates + TailwindCSS / Bootstrap
- Emails : SMTP via django-after-response (async)
- Admin : django-jazzmin
- Tâches asynchrones : Celery + Redis
