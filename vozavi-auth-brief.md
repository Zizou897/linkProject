# BRIEF — Pages de connexion et d'inscription de Vozavi

> Contexte de référence pour générer les écrans d'authentification de Vozavi.
> À utiliser avec le brief landing page (mêmes couleurs, mêmes polices, même ton).

---

## 1. Rappel produit

Vozavi est un SaaS **100 % gratuit** de création de formulaires d'avis et de feedback
(clients, employés, étudiants, participants d'événements). Cible : Afrique francophone,
trafic majoritairement **mobile**. Langue : **français**, vouvoiement, ton simple et chaleureux.

## 2. Identité visuelle (identique à la landing page)

- Indigo Vozavi `#4F46B8` (boutons primaires, liens), hover `#433CA0`
- Ambre étoile `#F2A93B` (étoile du logo uniquement ici)
- Fond de page : Lavande `#F4F3FB` — Carte du formulaire : blanc `#FFFFFF`
- Texte : Encre `#2C2C3A`, texte secondaire `#5F5E5A`
- Polices Google Fonts : Poppins (titres, 500/600), Inter (texte, 400/500)
- Coins arrondis : 14 px (carte), 10 px (boutons et champs)
- Logo Vozavi centré au-dessus de la carte (bulle indigo + étoile ambre + « vozavi »)

## 3. Architecture des écrans

Une **page unique `/auth`** avec deux modes basculables sans rechargement
(état `login` / `signup`), plus un mode `forgot-password`. Routes alias acceptées :
`/login` et `/signup` ouvrent la même page dans le bon mode.

### Mode CONNEXION (login)
- Titre : « Bon retour ! » — Sous-titre : « Connectez-vous pour retrouver vos formulaires »
- Bouton « Continuer avec Google » (logo Google officiel, bouton blanc bordé)
- Séparateur « ou »
- Champ E-mail (type email, placeholder « vous@exemple.com »)
- Champ Mot de passe avec lien « Oublié ? » aligné à droite du label,
  et icône œil pour afficher/masquer le mot de passe
- Bouton primaire pleine largeur : « Se connecter »
- Lien bas de carte : « Pas encore de compte ? **Inscrivez-vous gratuitement** »
- Sous la carte : « 100 % gratuit · Sans carte bancaire »

### Mode INSCRIPTION (signup)
- Titre : « Créez votre compte gratuit » — Sous-titre : « Votre premier formulaire est à 2 minutes »
- Bouton « Continuer avec Google »
- Séparateur « ou »
- Champ E-mail
- Champ Mot de passe UNIQUE (pas de champ de confirmation) avec indicateur de robustesse
  discret (barre fine : rouge `#E24B4A` < 8 caractères, ambre 8-11, vert `#1D9E75` ≥ 12)
- Bouton primaire : « Créer mon compte »
- Mention légale 12 px sous le bouton : « En créant un compte, vous acceptez nos
  Conditions d'utilisation et notre Politique de confidentialité. » (liens placeholders)
- Lien bas de carte : « Déjà un compte ? **Connectez-vous** »
- IMPORTANT : ne demander AUCUNE autre information (pas de nom, pas de téléphone,
  pas d'entreprise). Ces infos seront demandées plus tard dans l'app, à la création
  du premier formulaire.

### Mode MOT DE PASSE OUBLIÉ
- Titre : « Réinitialiser le mot de passe »
- Texte : « Entrez votre e-mail, nous vous enverrons un lien de réinitialisation. »
- Champ E-mail + bouton « Envoyer le lien »
- État de succès : message vert « Si un compte existe avec cet e-mail, le lien est parti.
  Vérifiez votre boîte de réception. » (formulation volontairement neutre pour ne pas
  révéler si l'e-mail existe — sécurité)
- Lien retour : « ← Retour à la connexion »

## 4. Comportements et validation

- Validation côté client en temps réel mais NON bloquante pendant la saisie :
  les erreurs n'apparaissent qu'au blur ou à la soumission.
- Messages d'erreur en français, sous le champ concerné, en rouge `#E24B4A`, 13 px :
  - « Cette adresse e-mail n'est pas valide. »
  - « Le mot de passe doit contenir au moins 8 caractères. »
  - Connexion échouée : « E-mail ou mot de passe incorrect. » (message unique,
    ne jamais préciser lequel des deux — sécurité)
  - Inscription avec e-mail existant : « Un compte existe déjà avec cet e-mail.
    Connectez-vous ou réinitialisez votre mot de passe. »
- Bouton en état de chargement pendant la soumission (spinner + désactivé),
  texte « Connexion… » / « Création… ».
- Après connexion/inscription réussie : redirection vers `/dashboard` (placeholder).
- Soumission possible avec la touche Entrée.

## 5. Backend attendu (Supabase Auth)

- `signInWithOAuth({ provider: 'google' })` pour Google
- `signUp({ email, password })` et `signInWithPassword({ email, password })`
- `resetPasswordForEmail(email)` pour la réinitialisation
- Si l'environnement ne permet pas Supabase, créer des fonctions mock
  `auth.login()`, `auth.signup()`, `auth.resetPassword()` clairement isolées
  dans un fichier `lib/auth.js` pour brancher Supabase plus tard.

## 6. Exigences techniques

- **Mobile-first** : la carte fait max 380 px de large, centrée, avec padding
  confortable ; parfaite sur écran 360 px.
- Accessibilité : labels associés aux champs (`for`/`id`), `aria-live="polite"`
  sur les messages d'erreur, focus visibles (anneau indigo), navigation clavier complète.
- Champs : hauteur 44 px minimum (cible tactile), `autocomplete` correct
  (`email`, `current-password`, `new-password`).
- Pas d'image stock, pas de splitscreen avec photo : page sobre, fond lavande,
  carte blanche centrée, logo au-dessus.
- Animations sobres : transition douce 200 ms au basculement login/signup
  (fondu, pas de slide agressif). Respecter `prefers-reduced-motion`.
- SEO minimal : `<title>` « Connexion — Vozavi », `noindex` acceptable sur ces pages.

## 7. Check-list finale

- [ ] Un seul champ mot de passe à l'inscription (pas de confirmation).
- [ ] Aucune donnée demandée à part e-mail + mot de passe.
- [ ] Bouton Google en premier, au-dessus du formulaire e-mail.
- [ ] Message d'erreur de connexion volontairement vague (sécurité).
- [ ] Message de réinitialisation neutre (ne révèle pas l'existence du compte).
- [ ] Carte impeccable sur 360 px de large, champs de 44 px de haut minimum.
- [ ] « 100 % gratuit · Sans carte bancaire » visible sous la carte.
