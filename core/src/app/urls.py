from django.urls import path, reverse_lazy
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    # Home
    path('', views.home, name='home'),
    path('robots.txt', views.robots_txt, name='robots_txt'),
    path('sitemap.xml', views.sitemap_xml, name='sitemap_xml'),
    path('llms.txt', views.llms_txt, name='llms_txt'),
    path('contact/', views.contact_view, name='contact'),
    path('og-image.png', views.og_image_view, name='og_image'),
    path('conditions-utilisation/', views.cgu_view, name='cgu'),
    path('confidentialite/', views.confidentialite_view, name='confidentialite'),
    path('blog/', views.blog_view, name='blog'),
    path('aide/', views.aide_view, name='aide'),

    # Authentification
    path('connexion/', views.login_view, name='login'),
    path('inscription/', views.signup_view, name='signup'),
    path('deconnexion/', views.logout_view, name='logout'),

    # Mot de passe oublié (vues intégrées Django)
    path('mot-de-passe/reinitialiser/', auth_views.PasswordResetView.as_view(
        template_name='account/password_reset.html',
        email_template_name='account/password_reset_email.html',
        subject_template_name='account/password_reset_subject.txt',
        success_url=reverse_lazy('password_reset_done'),
    ), name='password_reset'),
    path('mot-de-passe/reinitialiser/envoye/', auth_views.PasswordResetDoneView.as_view(
        template_name='account/password_reset_done.html',
    ), name='password_reset_done'),
    path('mot-de-passe/reinitialiser/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(
        template_name='account/password_reset_confirm.html',
        success_url=reverse_lazy('password_reset_complete'),
    ), name='password_reset_confirm'),
    path('mot-de-passe/reinitialiser/termine/', auth_views.PasswordResetCompleteView.as_view(
        template_name='account/password_reset_complete.html',
    ), name='password_reset_complete'),

    # Dashboard
    path('dashboard/', views.dashboard, name='dashboard'),
    path('dashboard/forms/', views.forms_list, name='forms_list'),
    path('dashboard/compte/', views.account_settings, name='account_settings'),
    path('dashboard/compte/supprimer/', views.delete_account, name='delete_account'),

    # ── VOZAVI FORM BUILDER ──────────────────────────────────────────────────
    path('new/', views.new_form, name='new_form'),
    path('forms/<int:pk>/edit/', views.edit_form, name='edit_form'),
    path('dashboard/forms/<int:pk>/delete/', views.delete_form, name='delete_form'),
    path('dashboard/forms/<int:pk>/duplicate/', views.duplicate_form, name='duplicate_form'),
    path('dashboard/forms/<int:pk>/toggle-status/', views.toggle_form_status, name='toggle_form_status'),
    path('dashboard/forms/<int:pk>/meta/', views.update_form_meta, name='update_form_meta'),
    path('dashboard/forms/<int:pk>/notify/', views.update_form_notify, name='update_form_notify'),
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
    path('dashboard/answers/<int:pk>/file/', views.answer_file_download, name='answer_file'),
    path('dashboard/forms/<int:pk>/results/export/csv/', views.export_results_csv, name='export_results_csv'),
    path('dashboard/forms/<int:pk>/results/export/excel/', views.export_results_excel, name='export_results_excel'),

    # ── PUBLIC FORMS ─────────────────────────────────────────────────────────
    path('f/demo/', views.demo_form, name='demo_form_url'),
    path('f/demo/merci/', views.demo_form_thanks, name='demo_form_thanks'),
    path('f/<slug:slug>/', views.public_form, name='public_form'),
    path('f/<slug:slug>/og-image.png', views.form_og_image_view, name='form_og_image'),
    path('f/<slug:slug>/merci/', views.public_form_thanks, name='public_form_thanks'),
]
