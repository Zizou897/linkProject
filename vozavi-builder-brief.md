# BRIEF POUR CLAUDE CODE — Vozavi : parcours de création de formulaire

> **Mission** : implémenter le parcours complet de création d'un formulaire d'avis
> dans le projet Django Vozavi, en 3 étapes maximum, à partir de **templates**
> OU **depuis zéro**, jusqu'à la génération du **lien public + QR code**.
> Ce brief complète le document `vozavi-django-setup.md` (stack, modèles, URLs) :
> s'y conformer strictement s'il est présent dans le projet.

---

## 1. Contexte produit

Vozavi est un SaaS 100 % gratuit de collecte d'avis et de feedback (clients,
employés, étudiants, participants). Cible : Afrique francophone, trafic
majoritairement mobile. Langue : français, vouvoiement, ton simple.

**Philosophie non négociable** : un utilisateur qui n'y connaît rien doit créer
son formulaire et obtenir son lien en **moins de 2 minutes**. Chaque écran, chaque
champ, chaque clic doit être justifié. En cas de doute entre deux solutions,
choisir la plus simple pour l'utilisateur.

**Stack** : Django 5, templates Django + HTMX + Alpine.js (CDN), SQLite en dev,
django-allauth pour l'auth, librairie Python `qrcode`. Pas de React, pas de build.

**Identité visuelle** : Indigo `#4F46B8` (primaire, hover `#433CA0`),
Ambre `#F2A93B` (étoiles/notes), Vert `#1D9E75`, Rouge `#E24B4A`,
fond Lavande `#F4F3FB`, texte Encre `#2C2C3A`, secondaire `#5F5E5A`.
Poppins (titres 500/600) + Inter (texte) via Google Fonts. Coins arrondis 10-12 px,
ombres très subtiles. Mobile-first impeccable à 360 px.

**Isolation des espaces** : toute vue privée porte `@login_required` et tout accès
à un `Form` filtre `user=request.user` (404 sinon). Aucune exception.

---

## 2. Le parcours en 3 étapes (structure imposée)

```
/dashboard/new  ──────►  /dashboard/forms/<id>/edit  ──────►  /dashboard/forms/<id>/share
ÉTAPE 1                  ÉTAPE 2                               ÉTAPE 3
Choisir un modèle        Personnaliser + ajuster               Lien + QR code
ou partir de zéro        les questions                         prêts à partager
```

Un indicateur de progression discret (1 — 2 — 3, points reliés, étape courante
en indigo) est affiché en haut des trois écrans.

---

### ÉTAPE 1 — `/dashboard/new` : choisir un modèle OU partir de zéro

- Titre : « Quel type d'avis voulez-vous recueillir ? »
- Grille de cartes (2 colonnes sur mobile) — **5 templates + 1 carte spéciale** :

| Carte | Icône | Description courte |
|---|---|---|
| Restaurant & commerce | 🍽️ | Avis clients via QR code sur table ou comptoir |
| Prestation de service | 💼 | Retour client après une mission |
| Boutique | 🛍️ | Avis après un achat en boutique ou en ligne |
| Satisfaction après livraison | 🚚 | Retour à chaud après une livraison |
| Feedback employés | 🏢 | Climat interne — anonyme par défaut |
| **Partir de zéro** | ➕ | Construisez votre formulaire librement |

- La carte « Partir de zéro » a une bordure pointillée pour se distinguer,
  mais **même taille et même importance visuelle** que les templates :
  c'est un chemin de premier rang, pas une option cachée.
- Un clic sur n'importe quelle carte crée immédiatement le formulaire en base
  (statut `draft`) et redirige vers l'éditeur. Pas d'écran intermédiaire.

**Contenu des templates** (à mettre dans `forms_app/templates_data.py`) :
chaque template fournit `title` + 3-4 questions pré-remplies pertinentes
(toujours : 1 question `rating` obligatoire en premier, 1 question `text`
facultative en dernier ; entre les deux selon le contexte : choix unique,
cases à cocher ou grille de critères).

**« Partir de zéro » n'est JAMAIS une page blanche** : le formulaire est créé
avec le titre « Donnez votre avis » et 2 questions de départ
(une note sur 5 obligatoire + un commentaire facultatif). L'utilisateur modifie
de l'existant, il ne crée pas face au vide.

---

### ÉTAPE 2 — `/dashboard/forms/<id>/edit` : personnaliser et ajuster

L'écran a DEUX zones, dans cet ordre :

#### Zone A — Personnalisation (3 champs, PAS UN DE PLUS)
1. **Nom de l'entreprise / organisation** (texte, ex. « Chez Aminata »)
2. **Logo** (upload image facultatif ; sans logo → avatar automatique avec les
   initiales du nom sur fond de la couleur choisie)
3. **Couleur principale** (5 pastilles prédéfinies : indigo #4F46B8,
   vert #1D9E75, orange #D85A30, rose #D4537E, bleu #378ADD + un color picker)

Ces 3 champs s'enregistrent automatiquement (HTMX, déclenché au changement,
indicateur discret « Enregistré ✓ »).

#### Zone B — Les questions (édition ultra-simple, règles strictes)
- Le **titre du formulaire** s'édite inline : clic sur le texte → input → blur = sauvegardé.
- Chaque **question est une carte** affichant : icône de son type, son libellé,
  un aperçu de sa réponse (étoiles, options...), et UNE SEULE rangée d'actions :
  - interrupteur « Obligatoire » (toggle)
  - flèches ▲▼ pour réordonner (ou poignée de drag si simple à faire en Alpine)
  - icône poubelle 🗑 pour supprimer (confirmation légère)
- **Édition inline** : clic sur le libellé → il devient un input, blur ou Entrée
  = sauvegardé via HTMX. AUCUN panneau latéral, AUCUNE modale de configuration.
- Pour les types à options (choix unique, cases à cocher, grille) : les options
  s'affichent sous le libellé, chacune éditable inline, avec un « + Ajouter une
  option » et un « × » par option.
- **Bouton « + Ajouter une question »** en bas de liste : ouvre un petit panneau
  inline (pas une modale) avec les 5 types illustrés :
  ⭐ Note / échelle · 🔘 Choix unique · ☑️ Cases à cocher · 💬 Texte libre ·
  📊 Grille de critères. Un clic = la question est ajoutée avec un libellé par
  défaut, prête à être éditée.
- Toute modification = requête HTMX qui renvoie le fragment HTML mis à jour.
  Jamais de rechargement de page complet pendant l'édition.

#### Bas d'écran (sticky sur mobile)
- Bouton secondaire « Aperçu » (ouvre le rendu du formulaire public dans un
  nouvel onglet, marqué « Aperçu — non publié »)
- Bouton primaire « **Publier** » → génère le slug, passe le statut à `active`,
  redirige vers l'étape 3.

---

### ÉTAPE 3 — `/dashboard/forms/<id>/share` : lien + QR, prêt à partager

- Titre : « Votre formulaire est en ligne 🎉 »
- **Le lien public** dans un champ en lecture seule + bouton « Copier »
  (feedback « Copié ✓ » vert pendant 2 s)
- **Le QR code** affiché en grand (généré par la vue Django `qr.png`),
  avec bouton « Télécharger le QR (PNG) » (attribut `download`)
- **Bouton « Partager sur WhatsApp »** :
  `https://wa.me/?text=` + message encodé « Donnez votre avis en 1 minute : [lien] »
- Lien discret « Retour au tableau de bord »
- Rappel sous le lien : « Toute personne disposant du lien peut répondre. »

---

## 3. Modèles de données (rappel — ne pas dévier)

`Form(user, title, slug unique nullable, status draft/active/closed, template_key,
brand_name, brand_color, logo ImageField nullable, is_anonymous, created_at)`

`Question(form, type ∈ {rating, single_choice, multiple_choice, text, grid},
label, required, position, options JSONField)`

Options selon type : rating → `{"max":5}` ; choix → `{"choices":[...]}` ;
grid → `{"criteria":[...], "max":5}`.

`Response(form, created_at)` · `Answer(response, question, value JSONField)`

---

## 4. Vues à implémenter (toutes filtrées par user)

| Vue | Méthode | Rôle |
|---|---|---|
| `new_form` | GET/POST | grille templates + zéro ; POST crée Form+Questions, redirect edit |
| `edit_form` | GET | écran éditeur complet |
| `update_form_meta` | POST (HTMX) | titre, nom, couleur, logo — autosave |
| `add_question` | POST (HTMX) | ajoute une question du type choisi |
| `update_question` | POST (HTMX) | libellé, obligatoire, options |
| `move_question` | POST (HTMX) | réordonne (échange de positions) |
| `delete_question` | POST (HTMX) | supprime |
| `publish_form` | POST | slug + statut active, redirect share |
| `share_form` | GET | lien, QR, WhatsApp |
| `qr_code` | GET | renvoie le PNG du QR |
| `preview_form` | GET | rendu public en mode aperçu (réservé au propriétaire) |

---

## 5. Critères d'acceptation (à vérifier un par un avant de livrer)

- [ ] Depuis le dashboard, je crée un formulaire via le template « Restaurant »
      et j'obtiens mon lien en 3 écrans, sans jamais être bloqué.
- [ ] « Partir de zéro » crée un formulaire avec titre + 2 questions de départ
      (jamais une page vide).
- [ ] L'étape 2 ne demande que 3 champs de personnalisation : nom, logo, couleur.
- [ ] Le libellé d'une question s'édite en cliquant dessus, sans modale ni panneau.
- [ ] « + Ajouter une question » propose les 5 types avec icônes, en un clic.
- [ ] Obligatoire (toggle), réordonner (▲▼), supprimer (🗑) : rien d'autre par question.
- [ ] « Publier » génère un slug court non devinable et le lien `/f/<slug>/` fonctionne
      en navigation privée (sans compte).
- [ ] Le QR code s'affiche, se télécharge en PNG, et encode bien le lien public.
- [ ] Le bouton WhatsApp ouvre wa.me avec le message pré-rempli.
- [ ] Test d'isolation : un 2ᵉ compte reçoit un 404 sur l'URL d'édition du 1ᵉʳ.
- [ ] Tout est impeccable sur un écran de 360 px de large.
- [ ] Étoiles ambre #F2A93B, boutons indigo #4F46B8, fond lavande #F4F3FB,
      Poppins/Inter chargées.

## 6. Hors périmètre (ne PAS implémenter maintenant)

Page de statistiques/réponses détaillée, exports, notifications, logique
conditionnelle, suppression du compte, déploiement. Rester concentré sur le
parcours création → publication → partage.
