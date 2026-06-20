# Onboarding — Accueil + premier formulaire guidé

Date : 2026-06-20
Statut : validé (design approuvé)
Portée : lot P2, item « onboarding » uniquement.

## Objectif

Activer un nouvel utilisateur juste après son inscription en le menant
directement vers la création de son premier formulaire, sans passer par
le dashboard vide. L'accueil et le choix du modèle tiennent sur **un seul
écran**, puis l'éditeur (déjà guidé par son stepper 3 étapes) prend le
relais.

## Décisions de cadrage

- **Forme** : écran d'accueil chaleureux qui débouche directement sur le
  choix du modèle (pas de visite guidée, pas de checklist, pas de modale).
- **Déclenchement** : uniquement **juste après l'inscription**. Aucune
  donnée persistée (pas de modèle/flag) ; l'état tient dans un paramètre
  d'URL. L'accueil ne réapparaît donc pas aux connexions suivantes.
- **Écran unique** : l'accueil et la grille de modèles sont sur la même
  page (`/new`), pas d'étape intermédiaire.

## Approche retenue

**Accueil conditionnel sur `/new`** — on réutilise la page de choix de
modèle existante (`vozavi/builder/new.html`) en lui ajoutant un en-tête
de bienvenue affiché conditionnellement. Aucune nouvelle page, aucun
nouveau modèle, aucune migration, aucune duplication de la grille de
modèles.

Approches écartées :
- Page dédiée `/bienvenue` : duplication de la grille (ou partial à
  extraire), surface en plus pour peu de gain.
- Modale Alpine : pièces mobiles supplémentaires, dépendance JS qu'on
  vient de fiabiliser.

## Détail technique

### 1. Redirection à l'inscription (`signup_view`)

Dans `core/src/app/views.py`, `signup_view` :

- Cas **inscription fraîche** (succès, sans `claim` de formulaire invité) :
  rediriger vers `new_form` avec le paramètre `?bienvenue=1` au lieu de
  `dashboard`.
- Cas **claim** (l'utilisateur avait créé un formulaire en invité) :
  comportement inchangé → redirection vers `share_form`.

Implémentation : construire l'URL via
`reverse('new_form') + '?bienvenue=1'` et renvoyer `redirect(url)`.

### 2. Vue `new_form` (GET)

Toujours dans `views.py`, `new_form` :

- Au GET, exposer au template :
  `welcome = (request.GET.get('bienvenue') == '1')`.
- Le POST de création (choix d'un modèle) reste **strictement inchangé**.

### 3. Template `new.html`

- Si `welcome` est vrai, remplacer le bloc `page-head` standard par un
  **hero de bienvenue** :
  - Titre : « Bienvenue sur Vozavi 👋 »
  - Sous-titre : « Créons votre premier formulaire. Choisissez un point
    de départ — vous pourrez tout personnaliser ensuite. »
  - Une fine bande rassurante en 3 mini-étapes : **Créez → Partagez →
    Écoutez** (cohérente avec le stepper du builder et la promesse de la
    marque).
- Sinon, l'en-tête actuel (« Quel type d'avis voulez-vous recueillir ? »)
  reste inchangé.
- La grille de modèles (`tpl-grid`) est commune aux deux cas — aucune
  duplication. Le lien « Retour » de l'en-tête pointe déjà vers le
  dashboard pour un utilisateur connecté.
- Style cohérent avec le design system Vozavi (Poppins/Inter, indigo
  `#4F46B8`, ambre `#F2A93B`), responsive mobile-first.

## Hors périmètre (YAGNI)

- Pas de checklist d'activation, pas de visite guidée, pas de coachmarks.
- Pas de suivi « onboardé » en base, pas de relance.
- Pas de personnalisation par prénom (l'inscription ne collecte pas le
  prénom ; salutation générique).
- Pas de modification du flux invité→claim ni de l'éditeur.

## Tests

Dans `core/src/app/tests.py` :

1. **Redirection après inscription** : une inscription valide (sans claim)
   redirige vers `new_form` avec `?bienvenue=1`.
2. **Hero affiché** : un GET de `/new?bienvenue=1` contient le titre de
   bienvenue (« Bienvenue sur Vozavi »).
3. **Pas de hero en visite normale** : un GET de `/new` (sans paramètre)
   ne contient pas le hero de bienvenue et affiche l'en-tête standard.
4. **Création intacte** : un POST de modèle depuis cette page crée bien le
   formulaire et redirige vers l'éditeur (déjà couvert, on vérifie la
   non-régression).

## Critères de réussite

- Un nouvel inscrit arrive sur un écran de bienvenue menant au choix du
  modèle, sans voir le dashboard vide.
- L'accueil n'apparaît qu'à l'inscription, jamais aux connexions
  suivantes ni en visite normale de `/new`.
- Aucune régression sur le flux invité, la création, ni l'éditeur.
- Suite de tests au vert.
