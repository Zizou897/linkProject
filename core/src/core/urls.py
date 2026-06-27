from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.conf.urls.static import static
from django.views.static import serve as media_serve

handler404 = 'app.views.custom_404'

urlpatterns = [
    path('vz-control-panel/', admin.site.urls),
    path('admin-vozavi/', include('backoffice.urls')),
    path('', include('app.urls')),
]

# Médias (uploads utilisateurs : logos de formulaires). WhiteNoise ne sert que
# STATIC_ROOT, et static() est neutralisé quand DEBUG=False — sans cette route,
# /media/ renvoie 404 en production (logo absent sur la page publique). On expose
# donc /media/ explicitement, y compris en prod (Gunicorn + WhiteNoise, sans nginx).
# Contrairement à WhiteNoise (index figé au démarrage), la vue serve prend en
# compte les fichiers uploadés à chaud.
urlpatterns += [
    re_path(r'^%s(?P<path>.*)$' % settings.MEDIA_URL.lstrip('/'),
            media_serve, {'document_root': settings.MEDIA_ROOT}),
]

# Statiques : WhiteNoise les sert en production ; static() couvre le développement.
urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
