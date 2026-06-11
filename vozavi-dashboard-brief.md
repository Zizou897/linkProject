# BRIEF — Tableau de bord de Vozavi (après connexion)

> Contexte de référence pour générer le dashboard de Vozavi.
> À utiliser avec les briefs précédents (landing page, auth) : mêmes couleurs,
> mêmes polices, même ton. Objectif : simple, complet, prise en main immédiate.

---

## 1. Rappel produit

Vozavi est un SaaS **100 % gratuit** de création de formulaires d'avis et de feedback
(clients, employés, étudiants, participants). Trafic majoritairement **mobile**.
Langue : **français**, vouvoiement, ton simple et chaleureux.

## 2. Identité visuelle (rappel)

- Indigo `#4F46B8` (primaire, hover `#433CA0`) · Ambre `#F2A93B` (étoiles, notes)
- Vert `#1D9E75` (positif) · Rouge `#E24B4A` (négatif/alertes)
- Fond de page Lavande `#F4F3FB` · Cartes blanches `#FFFFFF` · Texte Encre `#2C2C3A`,
  secondaire `#5F5E5A`
- Poppins (titres 500/600) + Inter (texte 400/500), coins arrondis 12 px,
  ombres très subtiles (`0 2px 8px rgba(44,44,58,0.06)`)

## 3. Architecture

Deux écrans + une modale :
1. **`/dashboard`** — accueil « Mes formulaires » (vue d'ensemble)
2. **`/dashboard/forms/[id]`** — détail d'un formulaire (réponses + statistiques)
3. **Modale « Partager »** — accessible depuis les deux écrans

Header commun (sticky) : logo Vozavi à gauche, à droite avatar rond indigo avec
les initiales de l'utilisateur ouvrant un menu (Mon compte, Se déconnecter).
PAS de sidebar : la navigation reste minimale, tout part de l'accueil.

---

## 4. Écran 1 — Accueil `/dashboard`

### 4.1 Salutation
« Bonjour [prénom] 👋 » (si le prénom est inconnu : « Bonjour 👋 »).

### 4.2 Trois indicateurs clés (cartes en ligne, 3 colonnes même sur mobile)
1. **Réponses** : total de réponses tous formulaires + delta « +X cette semaine » en vert.
2. **Note globale** : moyenne pondérée de tous les avis, format « 4,4 ★ » (étoile ambre),
   mention « sur 5 ».
3. **Formulaires** : nombre total + « X actifs ».

### 4.3 Bouton primaire pleine largeur
« + Nouveau formulaire » → redirige vers `/dashboard/new` (placeholder builder).
C'est l'action n°1 du produit, il doit être impossible à rater.

### 4.4 Liste « Mes formulaires » (cartes empilées)
Chaque carte affiche :
- Nom du formulaire + badge de statut : **Actif** (pill verte), **Brouillon** (pill grise),
  **Fermé** (pill grise foncée)
- Ligne de stats : note moyenne (★ ambre), nombre de réponses,
  et si > 0 : « X négatives » en rouge `#E24B4A` (négatif = note ≤ 2)
- Badge « Anonyme » gris si le formulaire est en mode réponses anonymes
- Deux boutons : **Partager** (secondaire) et **Voir les réponses** (primaire)
- Les brouillons ont une bordure pointillée, pas de stats, un seul bouton « Continuer l'édition »
- Menu « ⋯ » par carte : Renommer, Dupliquer, Fermer/Réactiver, Supprimer
  (suppression avec confirmation)

Tri par défaut : actifs d'abord, puis brouillons, puis fermés ; dans chaque groupe,
le plus récemment actif en premier.

### 4.5 ÉTAT VIDE (nouvel utilisateur — aussi soigné que l'état rempli)
Si aucun formulaire :
- Illustration légère en SVG (bulle + étoile du logo, grande, opacité douce)
- Titre : « Créez votre premier formulaire »
- Texte : « Choisissez un modèle prêt à l'emploi ou partez de zéro.
  Dans 2 minutes, vous partagez votre lien. »
- Grille des 4 templates directement affichée (Restaurant & commerce ·
  Prestation de service · Feedback employés · Évaluation de cours/formation)
  + une carte « Partir de zéro »
- PAS de tableaux vides, PAS de stats à zéro.

---

## 5. Écran 2 — Détail d'un formulaire `/dashboard/forms/[id]`

### 5.1 En-tête
- Fil d'Ariane « ← Mes formulaires », nom du formulaire, badge statut,
  boutons « Partager » (primaire) et « Modifier » (secondaire).

### 5.2 Bloc statistiques
- **Note moyenne** en grand (ex. « 4,6 ★ ») + nombre total de réponses.
- **Répartition des notes** : 5 barres horizontales (5★ → 1★), longueur proportionnelle,
  barres en ambre, les barres 1★ et 2★ en rouge si elles contiennent des réponses,
  avec le compte à droite de chaque barre.
- **Évolution** : mini graphique en ligne des réponses sur 30 jours (sobre, indigo).
- Si le formulaire contient des questions à choix : pour chacune, un petit graphique
  en barres horizontales des options les plus choisies.

### 5.3 Liste des réponses
- Filtres en pills : **Toutes** · **Positives** (≥ 4) · **Négatives** (≤ 2) · **Avec commentaire**
- Chaque réponse = carte : note en étoiles ambre, date relative (« il y a 2 h »),
  extrait du commentaire, et au clic dépliage de la réponse complète
  (toutes les questions/réponses).
- Réponses anonymes : aucune métadonnée identifiante affichée.
- Les réponses négatives ont un liseré gauche rouge 3 px.
- Pagination ou scroll infini par lots de 20.

### 5.4 État vide du détail
Si 0 réponse : « Aucune réponse pour l'instant. Partagez votre formulaire pour
recevoir vos premiers avis. » + bouton « Partager » + QR code affiché directement.

---

## 6. Modale « Partager »

- Lien public en lecture seule + bouton « Copier » (feedback « Copié ✓ » en vert 2 s)
- QR code généré côté client (librairie `qrcode`), boutons « Télécharger le QR (PNG) »
- Bouton « Partager sur WhatsApp » (vert WhatsApp accepté ici uniquement) :
  ouvre `https://wa.me/?text=` avec un message pré-rempli :
  « Donnez-nous votre avis en 1 minute : [lien] »
- Rappel discret : « Toute personne disposant du lien peut répondre. »

---

## 7. Données (mock à fournir)

Créer un fichier `lib/mockData.js` avec des données réalistes en français :
3 formulaires (« Avis clients — Restaurant » actif 86 réponses moyenne 4,6 dont 2 ≤ 2 ;
« Feedback équipe — Juin » actif anonyme 34 réponses moyenne 3,9 ;
« Évaluation formation » brouillon), et ~20 réponses variées avec commentaires
courts crédibles (ton ivoirien naturel bienvenu, sans caricature).
Structurer les données comme l'API future : `forms[]`, `responses[]`,
chaque réponse contenant `answers[]` liés aux `questions[]` du formulaire.

## 8. Exigences techniques

- **Mobile-first** impeccable sur 360 px ; sur desktop (> 900 px), l'accueil passe
  les cartes formulaires en grille 2 colonnes, le détail en 2 colonnes
  (stats à gauche, réponses à droite).
- Graphiques légers : barres en divs CSS, ligne 30 jours en SVG inline.
  PAS de librairie de charts lourde.
- Accessibilité : contrastes AA, focus visibles, `aria-label` sur les boutons icônes,
  les statistiques annoncées en texte (pas seulement visuelles).
- Performance : rendu instantané avec les mocks, squelettes de chargement
  (skeleton) prévus pour le branchement API.
- Nombres au format français : « 4,6 » (virgule), espaces fines pour milliers.
- Dates relatives en français (« il y a 2 h », « hier », « il y a 3 jours »).

## 9. Check-list finale

- [ ] L'état vide montre les templates, jamais un tableau vide.
- [ ] « + Nouveau formulaire » est l'élément le plus visible de l'accueil.
- [ ] Les avis négatifs (≤ 2) sont signalés en rouge sur les cartes ET filtrables au détail.
- [ ] Le badge « Anonyme » apparaît sur les formulaires concernés et aucune
      métadonnée identifiante n'est affichée sur leurs réponses.
- [ ] La modale Partager propose : copie du lien, QR téléchargeable, WhatsApp pré-rempli.
- [ ] Étoiles toujours ambre #F2A93B, boutons indigo #4F46B8, fond lavande #F4F3FB.
- [ ] Parfait sur 360 px de large ; grille 2 colonnes au-delà de 900 px.
