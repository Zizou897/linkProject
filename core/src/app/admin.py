from django.contrib import admin
from .models import Formation, LienSecurise, SessionPresentielle, Avis


@admin.register(Formation)
class FormationAdmin(admin.ModelAdmin):
    list_display = ('libelle', 'archive', 'created_at')
    list_filter = ('archive',)
    search_fields = ('libelle', 'descriptif')


@admin.register(LienSecurise)
class LienSecuriseAdmin(admin.ModelAdmin):
    list_display = ('label', 'token', 'actif', 'date_expiration', 'created_at')
    list_filter = ('actif',)
    readonly_fields = ('token',)
    filter_horizontal = ('formations',)


@admin.register(SessionPresentielle)
class SessionPresentielleAdmin(admin.ModelAdmin):
    list_display = ('formation', 'date', 'lieu', 'formateur', 'capacite', 'statut')
    list_filter = ('statut', 'formation')


@admin.register(Avis)
class AvisAdmin(admin.ModelAdmin):
    list_display = ('prenom', 'nom', 'structure', 'session', 'created_at')
    list_filter = ('session__formation',)
    search_fields = ('nom', 'prenom', 'email', 'structure')
