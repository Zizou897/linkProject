from django.urls import path
from . import views, exports

urlpatterns = [
    # Home
    path('', views.home, name='home'),

    # Authentification admin
    path('connexion/', views.login_view, name='login'),
    path('deconnexion/', views.logout_view, name='logout'),

    # Formulaire avis (public)
    path('avis/<str:token>/', views.avis_formation, name='avis_formation'),
    path('avis/<str:token>/merci/', views.avis_confirmation, name='avis_confirmation'),

    # Dashboard administrateur
    path('dashboard/', views.dashboard, name='dashboard'),

    # Gestion des formations
    path('formations/', views.formations_liste, name='formations_liste'),
    path('formations/creer/', views.formation_creer, name='formation_creer'),
    path('formations/<int:pk>/', views.formation_detail, name='formation_detail'),
    path('formations/<int:pk>/modifier/', views.formation_modifier, name='formation_modifier'),
    path('formations/<int:pk>/supprimer/', views.formation_supprimer, name='formation_supprimer'),
    path('formations/<int:pk>/archiver/', views.formation_archiver, name='formation_archiver'),
    path('formations/<int:formation_pk>/sessions/creer/', views.session_creer, name='session_creer_pour_formation'),

    # Module sessions
    path('sessions/', views.sessions_liste, name='sessions_liste'),
    path('sessions/creer/', views.session_creer, name='session_creer'),
    path('sessions/<int:pk>/', views.session_detail, name='session_detail'),
    path('sessions/<int:pk>/modifier/', views.session_modifier, name='session_modifier'),
    path('sessions/<int:pk>/cloturer/', views.cloturer_session, name='cloturer_session'),
    path('sessions/<int:pk>/regenerer-lien/', views.regenerer_lien, name='regenerer_lien'),

    # Exports Excel
    path('exports/avis/excel/', exports.export_avis_excel, name='export_avis_excel'),

    # Exports PDF
    path('sessions/<int:pk>/export/excel/', exports.export_session_excel, name='export_session_excel'),
    path('sessions/<int:pk>/export/pdf/', exports.export_session_pdf, name='export_session_pdf'),
    path('exports/rapport/pdf/', exports.export_rapport_pdf, name='export_rapport_pdf'),
]
