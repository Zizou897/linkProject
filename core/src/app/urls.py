from django.urls import path
from . import views

urlpatterns = [
    # Home
    path('', views.home, name='home'),
    path('contact/', views.contact_view, name='contact'),
    path('og-image.png', views.og_image_view, name='og_image'),
    path('conditions-utilisation/', views.cgu_view, name='cgu'),
    path('confidentialite/', views.confidentialite_view, name='confidentialite'),

    # Authentification
    path('connexion/', views.login_view, name='login'),
    path('inscription/', views.signup_view, name='signup'),
    path('deconnexion/', views.logout_view, name='logout'),

    # Dashboard
    path('dashboard/', views.dashboard, name='dashboard'),

    # ── VOZAVI FORM BUILDER ──────────────────────────────────────────────────
    path('new/', views.new_form, name='new_form'),
    path('forms/<int:pk>/edit/', views.edit_form, name='edit_form'),
    path('dashboard/forms/<int:pk>/meta/', views.update_form_meta, name='update_form_meta'),
    path('dashboard/forms/<int:pk>/questions/add/', views.add_question, name='add_question'),
    path('dashboard/forms/<int:pk>/questions/<int:qid>/update/', views.update_question, name='update_question'),
    path('dashboard/forms/<int:pk>/questions/<int:qid>/move/', views.move_question, name='move_question'),
    path('dashboard/forms/<int:pk>/questions/<int:qid>/delete/', views.delete_question, name='delete_question'),
    path('dashboard/forms/<int:pk>/publish/', views.publish_form, name='publish_form'),
    path('dashboard/forms/<int:pk>/share/', views.share_form, name='share_form'),
    path('dashboard/forms/<int:pk>/qr.png', views.qr_code_view, name='qr_code'),
    path('dashboard/forms/<int:pk>/preview/', views.preview_form, name='preview_form'),
    path('dashboard/forms/<int:pk>/results/', views.form_results, name='form_results'),
    path('dashboard/forms/<int:pk>/responses/', views.form_responses, name='form_responses'),
    path('dashboard/forms/<int:pk>/results/export/csv/', views.export_results_csv, name='export_results_csv'),
    path('dashboard/forms/<int:pk>/results/export/excel/', views.export_results_excel, name='export_results_excel'),

    # ── PUBLIC FORMS ─────────────────────────────────────────────────────────
    path('f/demo/', views.demo_form, name='demo_form_url'),
    path('f/demo/merci/', views.demo_form_thanks, name='demo_form_thanks'),
    path('f/<slug:slug>/', views.public_form, name='public_form'),
    path('f/<slug:slug>/og-image.png', views.form_og_image_view, name='form_og_image'),
    path('f/<slug:slug>/merci/', views.public_form_thanks, name='public_form_thanks'),
]
