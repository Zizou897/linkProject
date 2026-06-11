from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

handler404 = 'app.views.custom_404'

urlpatterns = [
    path('vz-control-panel/', admin.site.urls),
    path('tinymce/', include('tinymce.urls')),
    path('', include('app.urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT) \
  + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
