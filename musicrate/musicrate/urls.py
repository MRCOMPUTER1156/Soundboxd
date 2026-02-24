from core import views
from core.views import ArtistViewSet, AlbumViewSet, ReviewViewSet
from django.contrib import admin
from django.urls import path, include
from rest_framework.routers import DefaultRouter

router = DefaultRouter()
router.register(r'artists', ArtistViewSet)
router.register(r'albums', AlbumViewSet)
router.register(r'reviews', ReviewViewSet)

urlpatterns = [
    path("", views.home),
    path("albums/", views.album_list),
    path("admin/", admin.site.urls),
    path("api/", include(router.urls)),
    path("test-spotify/", views.test_spotify),
    path("login/", views.spotify_login),
    path("callback/", views.spotify_callback),
    path('search/', views.search, name='search'),
    path('spotify_logout/', views.spotify_logout, name='spotify_logout'),
]