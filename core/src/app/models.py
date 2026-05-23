import secrets
from django.db import models
from django.db.models import Q
from django.utils import timezone


class Convention(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    update_at = models.DateTimeField(auto_now=True)
    publish = models.BooleanField(default=False)

    class Meta:
        abstract = True


# ── CATALOGUE DE FORMATIONS ──────────────────────────────────────────────────

class Formation(Convention):
    libelle = models.CharField(max_length=255)
    descriptif = models.TextField()
    objectifs_pedagogiques = models.TextField()
    duree = models.CharField(max_length=100)
    public_cible = models.TextField()
    nombre_places = models.PositiveIntegerField(default=20)
    periode_previsionnelle = models.CharField(max_length=255, blank=True)
    cout = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    archive = models.BooleanField(default=False)

    class Meta:
        verbose_name = 'Formation'
        verbose_name_plural = 'Formations'
        ordering = ['libelle']

    def __str__(self):
        return self.libelle

    @property
    def is_active(self):
        """True si au moins une session a un lien actif et non expiré."""
        return self.sessions.filter(lien__actif=True).filter(
            Q(lien__date_expiration__isnull=True) |
            Q(lien__date_expiration__gt=timezone.now())
        ).exists()


# ── LIENS SÉCURISÉS ──────────────────────────────────────────────────────────

class LienSecurise(Convention):
    token = models.CharField(max_length=64, unique=True, editable=False)
    label = models.CharField(max_length=255)
    date_expiration = models.DateTimeField(null=True, blank=True)
    actif = models.BooleanField(default=True)
    formations = models.ManyToManyField(Formation, related_name='liens', blank=True)

    class Meta:
        verbose_name = 'Lien sécurisé'
        verbose_name_plural = 'Liens sécurisés'

    def __str__(self):
        return self.label

    def save(self, *args, **kwargs):
        if not self.token:
            self.token = secrets.token_urlsafe(32)
        super().save(*args, **kwargs)


# ── SESSIONS PRÉSENTIEL ───────────────────────────────────────────────────────

class SessionPresentielle(Convention):
    class Statut(models.TextChoices):
        PLANIFIEE = 'planifiee', 'Planifiée'
        EN_COURS = 'en_cours', 'En cours'
        CLOTUREE = 'cloturee', 'Clôturée'
        ANNULEE = 'annulee', 'Annulée'

    formation = models.ForeignKey(
        Formation, on_delete=models.CASCADE, related_name='sessions'
    )
    lien = models.OneToOneField(
        'LienSecurise', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='session'
    )
    public_cible = models.TextField(blank=True)
    periode_previsionnelle = models.CharField(max_length=255, blank=True)
    date = models.DateField()
    lieu = models.CharField(max_length=255)
    formateur = models.CharField(max_length=255)
    capacite = models.PositiveIntegerField()
    duree = models.CharField(max_length=100, blank=True)
    cout = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    statut = models.CharField(max_length=20, choices=Statut.choices, default=Statut.PLANIFIEE)

    class Meta:
        verbose_name = 'Session présentielle'
        verbose_name_plural = 'Sessions présentiel'
        ordering = ['date']

    def __str__(self):
        return f"{self.formation} — {self.date} ({self.lieu})"


# ── AVIS ──────────────────────────────────────────────────────────────────────

class Avis(models.Model):
    session = models.ForeignKey(
        SessionPresentielle, on_delete=models.CASCADE, related_name='avis'
    )
    nom = models.CharField(max_length=150)
    prenom = models.CharField(max_length=150)
    structure = models.CharField(max_length=255)
    fonction = models.CharField(max_length=255)
    email = models.EmailField()
    telephone = models.CharField(max_length=30, blank=True)
    zone_geographique = models.CharField(max_length=255, blank=True)
    motivations = models.TextField()
    probleme_professionnel = models.TextField(blank=True)
    competences_attendues = models.TextField(blank=True)
    contraintes_calendrier = models.CharField(max_length=255, blank=True)
    contrainte_mobilite = models.BooleanField(default=False)
    format_prefere = models.CharField(max_length=50, blank=True)
    observation = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Avis'
        verbose_name_plural = 'Avis'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.prenom} {self.nom} — {self.session.formation.libelle}"
