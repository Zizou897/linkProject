# BRIEF COMPLET — Landing page de Vozavi

> Ce document est le contexte de référence pour générer la landing page de Vozavi.
> Suis-le rigoureusement : identité, ton, structure, contenus et exigences techniques.
> Objectif : une landing page digne des grands SaaS (niveau Tally, Notion, Linear, Typeform).

---

## 1. Le produit

**Nom** : Vozavi
**Slogan principal** : « Donnez de la voix à vos avis »
**Tagline alternative** : « Créez un formulaire d'avis, partagez le lien, écoutez. »

**Définition** : Vozavi est un SaaS web **100 % gratuit** qui permet à n'importe qui — commerçant, entreprise, école, association, organisateur d'événement — de créer en moins de 2 minutes un formulaire d'avis ou de feedback personnalisé (logo, couleurs), puis de le diffuser via un lien public, un QR code ou WhatsApp, et de suivre les réponses dans un tableau de bord clair.

**Ce que Vozavi N'EST PAS** : ce n'est pas un outil réservé aux avis clients. C'est une plateforme universelle de collecte d'opinions et de feedback.

**Cas d'usage à mettre en avant (tous au même niveau)** :
1. **Commerces & restaurants** — avis clients via QR code sur table, comptoir, reçu.
2. **Entreprises & RH** — feedback des employés : climat social, satisfaction interne, retour sur un séminaire, baromètre d'équipe (réponses anonymes possibles).
3. **Écoles & universités** — avis des étudiants : évaluation des cours, des enseignants, de la cantine, de la vie sur le campus.
4. **Événements** — retour à chaud des participants d'une conférence, d'un mariage, d'un concert.
5. **Freelances & prestataires** — recueillir des témoignages clients après une mission.

**Marché prioritaire** : Afrique francophone, en commençant par la Côte d'Ivoire (Abidjan). La page doit être en **français**, avec un ton qui parle autant à un gérant de maquis qu'à un DRH ou un directeur d'école.

**Modèle** : 100 % gratuit. Pas de carte bancaire, pas d'essai limité, pas de piège. C'est un argument central — le répéter dans le hero, la section tarif et la FAQ.

---

## 2. Identité visuelle (à respecter strictement)

### Couleurs
| Rôle | Nom | Hex |
|---|---|---|
| Couleur principale (boutons, liens, titres accent) | Indigo Vozavi | `#4F46B8` |
| Accent notation / étoiles / highlights | Ambre étoile | `#F2A93B` |
| Succès, confirmations, avis positifs | Vert succès | `#1D9E75` |
| Alertes, avis négatifs | Rouge alerte | `#E24B4A` |
| Fonds doux de sections alternées | Fond lavande | `#F4F3FB` |
| Texte principal | Encre | `#2C2C3A` |
| Fond général | Blanc | `#FFFFFF` |

### Typographies (Google Fonts)
- **Poppins** (600 pour les titres, 500 pour les sous-titres)
- **Inter** (400 pour le texte courant, 500 pour les labels)

### Logo
- Concept : une **bulle de dialogue indigo** contenant une **étoile ambre** + le mot « vozavi » en minuscules, Poppins SemiBold, indigo.
- Reproduis-le en SVG inline dans le header (bulle arrondie avec pointe en bas à gauche, étoile 5 branches centrée).
- Favicon : carré arrondi indigo avec étoile ambre.

### Style général
- Design **flat, épuré, généreux en espace blanc**. Pas de dégradés criards, pas d'ombres lourdes. Ombres très subtiles autorisées sur les cartes (`0 2px 8px rgba(44,44,58,0.06)`).
- Coins arrondis : 12 px (cartes), 10 px (boutons), 999 px (badges/pills).
- Boutons primaires : fond indigo, texte blanc, hover légèrement plus foncé (`#433CA0`).
- Boutons secondaires : bordure indigo 1px, texte indigo, fond transparent.
- Illustrations : préférer des **mockups d'interface stylisés** (faux formulaires, fausses cartes d'avis avec étoiles ambre) construits en HTML/CSS ou SVG, plutôt que des images stock. Aucune photo de banque d'images générique.
- Les étoiles de notation sont TOUJOURS ambre `#F2A93B`.

---

## 3. Ton et voix

- **Tutoiement** (« Crée ton formulaire ») OU vouvoiement (« Créez votre formulaire ») — choisis le **vouvoiement** pour rassurer les entreprises et écoles, mais garde des phrases courtes et chaleureuses.
- Ton : simple, direct, confiant, sans jargon technique. Jamais de « solution innovante de digitalisation », plutôt « créez votre formulaire, partagez le lien, lisez les réponses ».
- Phrases courtes. Bénéfices avant fonctionnalités.
- Une pointe de chaleur locale est bienvenue (exemples concrets : restaurant à Abidjan, université, PME), sans tomber dans le folklore.

---

## 4. Structure de la page (sections dans cet ordre)

### 4.1 Header (sticky)
- Logo Vozavi à gauche.
- Liens : Fonctionnalités · Cas d'usage · Comment ça marche · FAQ.
- À droite : bouton secondaire « Se connecter » + bouton primaire « Créer mon formulaire — c'est gratuit ».
- Sur mobile : menu burger propre.

### 4.2 Hero
- **H1** : « Recueillez les avis de ceux qui comptent. En 2 minutes. »
- **Sous-titre** : « Clients, employés, étudiants, participants… Créez un formulaire d'avis à vos couleurs, partagez un lien ou un QR code, et suivez les réponses en temps réel. 100 % gratuit. »
- **CTA primaire** : « Créer mon formulaire gratuitement » — **CTA secondaire** : « Voir un exemple ».
- Sous les CTA, une ligne de réassurance : « ✓ Gratuit, sans carte bancaire  ✓ Aucune installation  ✓ Prêt en 2 minutes ».
- **Visuel hero** : mockup d'un téléphone affichant un formulaire d'avis (note 5 étoiles ambre sélectionnée, champ commentaire), à côté d'une carte « tableau de bord » montrant une note moyenne 4,6/5 et un mini graphique à barres. Construis ce mockup en HTML/CSS.

### 4.3 Barre de cas d'usage (social proof de contexte)
Une rangée de 5 pills avec icônes : Restaurants & commerces · Entreprises & RH · Écoles & universités · Événements · Freelances.

### 4.4 Section « Comment ça marche » (3 étapes)
1. **Choisissez un modèle ou partez de zéro** — modèles prêts à l'emploi : avis client, feedback employé, évaluation de cours, retour d'événement.
2. **Personnalisez en 30 secondes** — votre logo, votre nom, votre couleur. Rien d'autre à configurer.
3. **Partagez et écoutez** — lien unique, QR code à imprimer, partage WhatsApp en un clic. Les réponses arrivent en temps réel.
Chaque étape : numéro dans un cercle lavande, titre Poppins, texte court, petit visuel mockup.

### 4.5 Section « Fonctionnalités » (grille de 6 cartes)
1. **5 types de questions** — note par étoiles, choix unique, cases à cocher, texte libre, grille de critères.
2. **Vos couleurs, votre logo** — le formulaire ressemble à votre marque, pas à la nôtre.
3. **QR code inclus** — téléchargez-le, imprimez-le, collez-le. Vos répondants scannent et répondent.
4. **Réponses anonymes** — idéal pour le feedback des employés et des étudiants en toute franchise.
5. **Tableau de bord clair** — note moyenne, répartition, commentaires. L'essentiel, sans fouillis.
6. **Pensé pour le mobile** — vos répondants répondent depuis leur téléphone, même avec une connexion moyenne.

### 4.6 Section « Cas d'usage » (3 cartes détaillées + témoignages fictifs réalistes)
- **Le restaurant** : « Le QR code est sur chaque table. Je sais le soir même si le service a plu. » — Aminata, gérante de restaurant, Abidjan.
- **L'entreprise** : « Chaque trimestre, nos 40 employés répondent anonymement. Les vrais sujets remontent enfin. » — Yao, DRH d'une PME.
- **L'université** : « Les étudiants évaluent chaque cours en fin de semestre. Les enseignants ont un retour concret. » — Dr Koné, directeur pédagogique.
(Présente-les comme des exemples d'utilisation illustratifs, pas comme de vrais clients.)

### 4.7 Section « Gratuit » (remplace la section pricing classique)
- Titre : « Combien ça coûte ? Rien. »
- Texte : « Vozavi est 100 % gratuit : formulaires illimités en création, lien et QR code inclus, tableau de bord complet. Pas de carte bancaire, pas de période d'essai, pas de surprise. »
- Une seule grande carte centrée style pricing « 0 FCFA / pour toujours » avec liste de ce qui est inclus et CTA « Commencer gratuitement ».

### 4.8 FAQ (accordéon, 6 questions)
1. Vozavi est-il vraiment gratuit ? → Oui, entièrement. Aucune carte bancaire demandée.
2. Mes répondants doivent-ils créer un compte ? → Non, ils cliquent sur le lien (ou scannent le QR code) et répondent. C'est tout.
3. Les réponses peuvent-elles être anonymes ? → Oui, c'est une option par formulaire, idéale pour le feedback interne.
4. Puis-je mettre mon logo et mes couleurs ? → Oui, c'est le cœur de Vozavi : le formulaire est à votre image.
5. Ça fonctionne sur mobile ? → Oui, les formulaires sont conçus d'abord pour le téléphone.
6. Combien de réponses puis-je recevoir ? → Autant que nécessaire pour un usage normal.

### 4.9 CTA final
- Bandeau indigo pleine largeur, logo version inversée, titre blanc : « Prêt à écouter ? », sous-titre : « Créez votre premier formulaire maintenant. C'est gratuit, pour de vrai. », bouton blanc texte indigo « Créer mon formulaire ».

### 4.10 Footer
- Logo + tagline, colonnes : Produit (Fonctionnalités, Cas d'usage, FAQ) · Ressources (Blog, Aide) · Légal (Confidentialité, Conditions) · Contact.
- Mention : « © 2026 Vozavi — Fait avec ❤ à Abidjan ».

---

## 5. Exigences techniques

- **Une seule page** HTML/CSS/JS, responsive **mobile-first** (la majorité du trafic sera mobile).
- Charger Poppins et Inter via Google Fonts avec `display=swap`.
- Performance : pas de librairie lourde, pas d'images stock ; mockups en HTML/CSS/SVG. Objectif Lighthouse > 90.
- Accessibilité : contrastes AA, attributs `alt`/`aria-label`, navigation clavier, HTML sémantique (`header`, `main`, `section`, `footer`).
- SEO : `<title>` « Vozavi — Formulaires d'avis et de feedback gratuits, en 2 minutes », meta description, balises Open Graph, un seul H1, hiérarchie H2/H3 propre, attribut `lang="fr"`.
- Animations : sobres et utiles uniquement (fade-in léger au scroll, transitions 150-250 ms). Respecter `prefers-reduced-motion`.
- Les CTA pointent vers `/signup` (placeholder) et « Voir un exemple » vers `/f/demo` (placeholder).
- Aucun texte en lorem ipsum : utiliser exclusivement les contenus de ce brief.

---

## 6. Check-list finale avant livraison

- [ ] Le mot « gratuit » apparaît dans le hero, la section prix et la FAQ.
- [ ] Les 5 publics (commerces, entreprises, écoles, événements, freelances) sont visibles dès le premier écran ou juste en dessous.
- [ ] Les étoiles sont ambre #F2A93B, les boutons indigo #4F46B8.
- [ ] La page est impeccable sur un écran de 360 px de large.
- [ ] Aucune photo stock, uniquement des mockups stylisés.
- [ ] Le ton vouvoie, reste simple et chaleureux, zéro jargon.
