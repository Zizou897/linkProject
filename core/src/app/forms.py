from django import forms
from .models import SessionPresentielle, Formation, Avis, Theme


class SessionPresentielleForm(forms.ModelForm):

    date_expiration_lien = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        label="Date d'expiration du lien",
        help_text="Laissez vide pour 90 jours par défaut.",
    )

    class Meta:
        model = SessionPresentielle
        fields = [
            'formation',
            'public_cible', 'periode_previsionnelle',
            'date', 'lieu', 'formateur', 'capacite', 'duree', 'cout',
            'statut',
        ]
        widgets = {
            'formation': forms.Select(attrs={'class': 'form-select'}),
            'public_cible': forms.Textarea(attrs={
                'class': 'form-control', 'rows': 2,
                'placeholder': 'Ex : Médecins, infirmiers, professionnels de santé...'
            }),
            'periode_previsionnelle': forms.TextInput(attrs={
                'class': 'form-control', 'placeholder': 'Ex : Octobre 2025, T1 2026...'
            }),
            'date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'lieu': forms.TextInput(attrs={
                'class': 'form-control', 'placeholder': 'Ex : Hôtel Laico, Yaoundé'
            }),
            'formateur': forms.TextInput(attrs={
                'class': 'form-control', 'placeholder': 'Nom du formateur'
            }),
            'capacite': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
            'duree': forms.TextInput(attrs={
                'class': 'form-control', 'placeholder': 'Ex : 3 jours / 21 heures'
            }),
            'cout': forms.NumberInput(attrs={
                'class': 'form-control', 'placeholder': 'Laisser vide si gratuit', 'min': 0
            }),
            'statut': forms.Select(attrs={'class': 'form-select'}),
        }
        labels = {
            'formation': 'Formation *',
            'public_cible': 'Public cible',
            'periode_previsionnelle': 'Période prévisionnelle',
            'date': 'Date *',
            'lieu': 'Lieu *',
            'formateur': 'Formateur *',
            'capacite': 'Nombre de places *',
            'duree': 'Durée',
            'cout': 'Coût (FCFA)',
            'statut': 'Statut',
        }


class FormationForm(forms.ModelForm):
    class Meta:
        model = Formation
        fields = ['libelle', 'descriptif', 'objectifs_pedagogiques']
        widgets = {
            'libelle': forms.TextInput(attrs={
                'class': 'form-control', 'placeholder': 'Intitulé de la formation'
            }),
            'descriptif': forms.Textarea(attrs={
                'class': 'form-control', 'rows': 4,
                'placeholder': 'Description générale de la formation...'
            }),
            'objectifs_pedagogiques': forms.Textarea(attrs={
                'class': 'form-control', 'rows': 4,
                'placeholder': 'Objectifs pédagogiques attendus...'
            }),
        }
        labels = {
            'libelle': 'Intitulé *',
            'descriptif': 'Description *',
            'objectifs_pedagogiques': 'Objectifs pédagogiques *',
        }


class AvisForm(forms.ModelForm):

    themes = forms.ModelMultipleChoiceField(
        queryset=Theme.objects.none(),
        required=False,
        widget=forms.CheckboxSelectMultiple(),
        label='Thèmes d\'intérêt',
    )

    def __init__(self, *args, formation=None, **kwargs):
        super().__init__(*args, **kwargs)
        if formation:
            self.fields['themes'].queryset = formation.themes.all()

    class Meta:
        model = Avis
        fields = [
            'nom', 'prenom', 'structure', 'fonction', 'email', 'telephone', 'zone_geographique',
            'motivations', 'probleme_professionnel', 'competences_attendues',
            'contraintes_calendrier', 'contrainte_mobilite', 'format_prefere', 'observation',
            'themes',
        ]
        widgets = {
            'nom': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nom'}),
            'prenom': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Prénom'}),
            'structure': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Organisation / entreprise'}),
            'fonction': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Fonction / poste'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Adresse email'}),
            'telephone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Téléphone (optionnel)'}),
            'zone_geographique': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ville / Pays (optionnel)'}),
            'motivations': forms.Textarea(attrs={
                'class': 'form-control', 'rows': 3,
                'placeholder': 'Pourquoi cette formation vous intéresse-t-elle ?'
            }),
            'probleme_professionnel': forms.Textarea(attrs={
                'class': 'form-control', 'rows': 3,
                'placeholder': 'Quel problème professionnel cherchez-vous à résoudre ?'
            }),
            'competences_attendues': forms.Textarea(attrs={
                'class': 'form-control', 'rows': 3,
                'placeholder': 'Quelles compétences attendez-vous à l\'issue de la formation ?'
            }),
            'contraintes_calendrier': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ex : pas disponible en juillet, préférence matin...'
            }),
            'contrainte_mobilite': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'format_prefere': forms.Select(
                choices=[
                    ('', '-- Choisir un format --'),
                    ('presentiel', 'Présentiel'),
                    ('distanciel', 'Distanciel'),
                    ('hybride', 'Hybride'),
                ],
                attrs={'class': 'form-select'}
            ),
            'observation': forms.Textarea(attrs={
                'class': 'form-control', 'rows': 2,
                'placeholder': 'Toute autre observation...'
            }),
        }
        labels = {
            'nom': 'Nom *', 'prenom': 'Prénom *',
            'structure': 'Structure / Organisation *', 'fonction': 'Fonction *',
            'email': 'Email *', 'telephone': 'Téléphone', 'zone_geographique': 'Zone géographique',
            'motivations': 'Motivations *',
            'probleme_professionnel': 'Problème professionnel visé',
            'competences_attendues': 'Compétences attendues',
            'contraintes_calendrier': 'Contraintes de calendrier',
            'contrainte_mobilite': 'Je ne peux pas me déplacer',
            'format_prefere': 'Format préféré',
            'observation': 'Observations libres',
        }
