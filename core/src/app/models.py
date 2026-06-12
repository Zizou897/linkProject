import secrets
from django.db import models
from django.contrib.auth.models import User


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
