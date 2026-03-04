from core import views
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static


# REST API endpoints were removed; keep simple views only

urlpatterns = [
    path("", views.home, name='home'),
    path("admin/", admin.site.urls),
    path('search/', views.search, name='search'),
    path('signup/', views.signup, name='signup'),
    path('rate/', views.rate_video, name='rate'),
    path('accounts/', include('django.contrib.auth.urls')),
    path('perfil/', views.perfil, name='perfil'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
