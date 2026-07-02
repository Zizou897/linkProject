# Type de question « Fichier » — Design

**Date** : 2026-07-02 · **Statut** : approuvé par le product owner

## Objectif
Permettre aux créateurs de formulaires de recevoir des documents de leurs
répondants (CV, justificatifs, devis…), avec une limite stricte de **4 Mo**.

## Décisions
| Sujet | Décision |
|---|---|
| Formats acceptés | PDF, Word (doc/docx), Excel (xls/xlsx), images (jpg/jpeg/png/webp) |
| Taille max | 4 Mo (validation serveur, `4 * 1024 * 1024` octets) |
| Fichiers par question | 1 |
| Accès aux documents | Créateur connecté uniquement (vue protégée) |

## Architecture
- **Stockage privé** : `Answer.file = FileField` sur un `FileSystemStorage`
  pointant vers `BASE_DIR/private_media/` (gitignoré, **hors** de `/media/`
  qui est servi publiquement). `upload_to='responses/%Y/%m/'`.
- **Métadonnées** dans `Answer.value` (JSON existant) : `{"name": <nom original>, "size": <octets>}`
  — affichage et exports sans toucher au disque.
- **Nettoyage disque** : signal `post_delete` sur `Answer` supprime le fichier.
- **Téléchargement** : route `dashboard/answers/<pk>/file/`, `@login_required`,
  404 si `answer.question.form.user != request.user`. `FileResponse` avec le
  nom original en pièce jointe.

## Points d'intégration
1. `Question.TYPE_CHOICES` += `('file', 'Fichier')` ; défauts dans `add_question`.
2. `add_panel.html` : bouton 📎 « Fichier » (pattern HTMX identique aux autres).
3. `form.html` public : `enctype="multipart/form-data"`, `<input type="file" accept=…>`,
   mention « PDF, Word, Excel ou image — 4 Mo max ».
4. `public_form` (phase 1) : validation extension (liste blanche) + taille + requis ;
   (phase 2) : sauvegarde du fichier sur l'Answer.
5. `_compute_question_stats` : cas `file` (compte + liste des fichiers).
6. `responses.html` / `results.html` : lien de téléchargement 📎.
7. Exports CSV/Excel : nom du fichier original.

## Limites assumées
- Un `input file` ne peut pas être pré-rempli : si la validation échoue sur un
  autre champ, le répondant re-sélectionne son fichier (comportement standard).
- Le formulaire démo n'inclut pas de question fichier (il n'enregistre rien).

## Tests
Upload OK · > 4 Mo rejeté · extension interdite rejetée · requis vide rejeté ·
téléchargement propriétaire = 200 · autre utilisateur = 404 · anonyme = redirect login.
