# Product

## Register

product

## Users

Deux populations distinctes :

- **Créateurs de formulaires** (app principale `/dashboard`) : TPE, associations, indépendants francophones qui créent des formulaires/sondages Vozavi et consultent leurs réponses. Peu techniques, sur mobile comme desktop.
- **Super-utilisateur / fondateur** (back-office `/admin-vozavi/`) : le concepteur du SaaS qui observe le comportement du produit en quasi-temps réel — KPI, funnel d'activation, utilisateurs, journal d'événements, messages de contact, santé technique — et agit sur les comptes. Contexte : sessions de pilotage courtes et fréquentes, souvent en parallèle d'autres tâches ; besoin de lire vite, en confiance.

## Product Purpose

Vozavi (vozavi.online) est un SaaS français de création de formulaires et de collecte de réponses. Le back-office est sa tour de contrôle : répondre en un coup d'œil à « le produit vit-il ? », « qui fait quoi ? », « qu'est-ce qui échoue ? », et permettre les actions d'administration (comptes, messages) sans passer par le Django admin brut.

## Brand Personality

Calme, dense, digne de confiance. L'outil s'efface derrière la tâche : lecture rapide de chiffres et de listes, hiérarchie nette, zéro décorum. Référence de registre : la sobriété opérationnelle de Linear et Stripe Dashboard — familiarité gagnée, pas d'étrangeté gratuite.

## Anti-references

- Le Django admin par défaut (tables grises sans hiérarchie).
- Les dashboards « template Bootstrap admin » : grilles de cartes identiques, icônes décoratives partout, gradients gratuits, hero-metrics tape-à-l'œil.
- Tout ce qui ressemble à du marketing dans une surface de travail (animations d'entrée orchestrées, typographie display dans les labels).

## Design Principles

1. **Lecture d'abord** : chaque écran doit répondre à sa question en moins de 5 secondes ; les chiffres portent des comparaisons (delta, tendance), jamais des valeurs nues.
2. **Vocabulaire unique** : mêmes boutons, badges, tables, états vides et densité sur toutes les surfaces admin ; un composant qui diverge est un bug.
3. **L'accent signifie** : l'indigo de marque marque l'action primaire, la sélection et l'état — jamais la décoration. La sémantique (vert/ambre/rouge) est réservée aux états réels.
4. **Le temps réel discret** : les rafraîchissements htmx sont invisibles (pas de flash, pas de spinner central) ; le mouvement signale un changement d'état, en 150–250 ms.
5. **Identité préservée** : tokens de marque Vozavi (indigo #4F46B8, point ambre, Poppins/Inter) ; le back-office est une déclinaison sombre-rail/canvas-clair de la marque, pas un thème étranger.

## Accessibility & Inclusion

- Contrastes AA vérifiés (corps ≥ 4.5:1, grands textes ≥ 3:1), y compris placeholders et texte sur fonds teintés.
- `prefers-reduced-motion` respecté sur toute animation/transition.
- Navigation clavier complète : focus visible partout, raccourci recherche (Ctrl/⌘K), cibles tactiles ≥ 40px sur mobile.
- Interface en français ; nombres en chiffres tabulaires pour la lecture en colonne.
