#!/usr/bin/env bash
#
# Déploiement Vozavi (serveur de production).
# À lancer sur le VPS : bash /var/www/linkProject/deploy.sh
#
# Enchaîne, dans l'ordre :
#   1. git pull            — récupère le code
#   2. pip install         — met à jour les dépendances
#   3. migrate             — applique les migrations base de données
#   4. collectstatic       — régénère les fichiers statiques (CSS/JS hashés + manifeste)
#   5. restart gunicorn    — recharge l'app (Django relit le manifeste, WhiteNoise ré-indexe)
#
# L'étape 4 (--clear) est la clé du bug d'affichage du back-office : sans elle, le
# manifeste et les fichiers hashés servis se désynchronisent et le CSS renvoie 404.
#
set -euo pipefail

# ── Configuration (adapter ici si l'infrastructure change) ──────────────
REPO_DIR="/var/www/linkProject"
VENV="/var/www/linkProject/venv"
SRC_DIR="/var/www/linkProject/core/src"                 # dossier contenant manage.py et .env
REQUIREMENTS="/var/www/linkProject/core/requirements.txt"
SERVICE="gunicorn_vozavi.service"

PY="$VENV/bin/python"
PIP="$VENV/bin/pip"

echo "▶ 1/5  git pull"
git -C "$REPO_DIR" pull --ff-only

echo "▶ 2/5  Dépendances Python"
"$PIP" install -r "$REQUIREMENTS" --quiet

# On se place dans SRC_DIR pour que python-decouple trouve le .env de production.
cd "$SRC_DIR"

echo "▶ 3/5  Migrations base de données"
"$PY" manage.py migrate --noinput

echo "▶ 4/5  Fichiers statiques (collectstatic --clear)"
"$PY" manage.py collectstatic --noinput --clear

echo "▶ 5/5  Redémarrage de $SERVICE"
sudo systemctl restart "$SERVICE"

echo "✅ Déploiement terminé."
