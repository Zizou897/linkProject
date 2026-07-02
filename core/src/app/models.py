import secrets
from django.conf import settings
from django.core.files.storage import FileSystemStorage
from django.db import models
from django.db.models.signals import post_delete
from django.dispatch import receiver
from django.contrib.auth.models import User


def private_storage():
    """Stockage des documents envoyés par les répondants.

    Hors de MEDIA_ROOT : /media/ est servi publiquement (urls.py), alors que
    ces documents ne doivent être téléchargeables que par le créateur du
    formulaire, via la vue protégée answer_file_download. Callable (et non
    instance) pour que la migration sérialise une référence, pas un chemin
    absolu propre à la machine.
    """
    return FileSystemStorage(location=str(settings.PRIVATE_MEDIA_ROOT))


class Convention(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    update_at = models.DateTimeField(auto_now=True)
    publish = models.BooleanField(default=False)

    class Meta:
        abstract = True


# ── VOZAVI FORM BUILDER ───────────────────────────────────────────────────────

class VozaviForm(models.Model):
    STATUS_CHOICES = [('draft', 'Brouillon'), ('active', 'Actif'), ('closed', 'Fermé')]
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='vozavi_forms', null=True, blank=True)
    title = models.CharField(max_length=255)
    slug = models.CharField(max_length=64, unique=True, null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft', db_index=True)
    template_key = models.CharField(max_length=50, blank=True)
    brand_name = models.CharField(max_length=255, blank=True)
    description = models.TextField(blank=True)
    brand_color = models.CharField(max_length=7, default='#4F46B8')
    logo = models.ImageField(upload_to='logos/', null=True, blank=True)
    is_anonymous = models.BooleanField(default=False)
    notify_responses = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.title


class Question(models.Model):
    TYPE_CHOICES = [
        ('rating', 'Note'),
        ('single_choice', 'Choix unique'),
        ('multiple_choice', 'Cases à cocher'),
        ('text', 'Texte libre'),
        ('grid', 'Grille de critères'),
        ('contact', 'Infos personnelles'),
        ('file', 'Fichier'),
    ]
    form = models.ForeignKey(VozaviForm, on_delete=models.CASCADE, related_name='questions')
    type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    label = models.CharField(max_length=500)
    required = models.BooleanField(default=False)
    position = models.PositiveIntegerField(default=0)
    options = models.JSONField(default=dict)

    class Meta:
        ordering = ['position']
        indexes = [models.Index(fields=['form', 'position'])]

    def __str__(self):
        return self.label


class VozaviResponse(models.Model):
    form = models.ForeignKey(VozaviForm, on_delete=models.CASCADE, related_name='responses')
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)


class Answer(models.Model):
    response = models.ForeignKey(VozaviResponse, on_delete=models.CASCADE, related_name='answers')
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    value = models.JSONField()
    # Document envoyé par le répondant (questions de type 'file'). Le nom
    # original et la taille sont conservés dans value ({"name": ..., "size": ...}).
    file = models.FileField(storage=private_storage, upload_to='responses/%Y/%m/', blank=True)


@receiver(post_delete, sender=Answer)
def _delete_answer_file(sender, instance, **kwargs):
    """Supprime le document du disque quand la réponse disparaît (suppression
    d'une réponse, d'un formulaire ou d'un compte — cascades comprises)."""
    if instance.file:
        instance.file.delete(save=False)


# ── PAGE CONTACT ──────────────────────────────────────────────────────────────

class ContactMessage(models.Model):
    CATEGORY_CHOICES = [
        ('general', 'Question générale'),
        ('support', 'Support technique'),
        ('billing', 'Facturation'),
        ('partnership', 'Partenariat'),
        ('other', 'Autre'),
    ]
    name = models.CharField(max_length=150)
    email = models.EmailField()
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES, blank=True)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Message de contact'
        verbose_name_plural = 'Messages de contact'

    def __str__(self):
        return f"{self.name} — {self.email} ({self.created_at.strftime('%d/%m/%Y')})"


# ── JOURNALISATION (back-office) ──────────────────────────────────────────────

class ActivityEvent(models.Model):
    EVENT_CHOICES = [
        ('user_signup', 'Inscription'),
        ('user_login', 'Connexion'),
        ('user_logout', 'Déconnexion'),
        ('account_deleted', 'Compte supprimé'),
        ('guest_form_claimed', 'Formulaire invité réclamé'),
        ('form_created', 'Formulaire créé'),
        ('form_published', 'Formulaire publié'),
        ('form_closed', 'Formulaire fermé'),
        ('form_reopened', 'Formulaire rouvert'),
        ('form_duplicated', 'Formulaire dupliqué'),
        ('form_deleted', 'Formulaire supprimé'),
        ('response_received', 'Réponse reçue'),
        ('contact_message', 'Message de contact'),
        ('email_sent', 'E-mail envoyé'),
        ('email_failed', 'E-mail échoué'),
        ('account_deactivated', 'Compte désactivé (admin)'),
        ('account_reactivated', 'Compte réactivé (admin)'),
        ('account_deleted_by_admin', 'Compte supprimé (admin)'),
    ]
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    event_type = models.CharField(max_length=40, choices=EVENT_CHOICES, db_index=True)
    actor = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL,
                              related_name='activity_events')
    target_type = models.CharField(max_length=40, blank=True)
    target_id = models.PositiveIntegerField(null=True, blank=True)
    label = models.CharField(max_length=255, blank=True)
    success = models.BooleanField(default=True)
    ip = models.GenericIPAddressField(null=True, blank=True)
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['event_type', 'created_at']),
            models.Index(fields=['actor', 'created_at']),
        ]

    def __str__(self):
        return f"{self.event_type} · {self.label or self.actor or '—'}"
