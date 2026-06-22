from django.urls import path
from . import views

urlpatterns = [
    path('', views.overview, name='bo_overview'),
    path('partials/kpis/', views.kpis_partial, name='bo_kpis_partial'),
    path('users/', views.users_list, name='bo_users'),
    path('journal/', views.journal, name='bo_journal'),
    path('health/', views.health, name='bo_health'),
]
