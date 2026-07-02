from django.urls import path
from . import views

urlpatterns = [
    path('login/', views.bo_login, name='bo_login'),
    path('logout/', views.bo_logout, name='bo_logout'),
    path('', views.overview, name='bo_overview'),
    path('partials/kpis/', views.kpis_partial, name='bo_kpis_partial'),
    path('users/', views.users_list, name='bo_users'),
    path('users/<int:pk>/', views.user_detail, name='bo_user_detail'),
    path('users/<int:pk>/toggle-active/', views.user_toggle_active, name='bo_user_toggle'),
    path('users/<int:pk>/delete/', views.user_delete, name='bo_user_delete'),
    path('search/', views.search, name='bo_search'),
    path('contacts/', views.contacts, name='bo_contacts'),
    path('contacts/<int:pk>/toggle-read/', views.contact_toggle_read, name='bo_contact_toggle'),
    path('contacts/<int:pk>/delete/', views.contact_delete, name='bo_contact_delete'),
    path('journal/', views.journal, name='bo_journal'),
    path('partials/journal-feed/', views.journal_feed, name='bo_journal_feed'),
    path('health/', views.health, name='bo_health'),
]
