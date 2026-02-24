import requests
from django.conf import settings
from django.shortcuts import render, redirect
from django.db.models import Q
from django.http import JsonResponse
from rest_framework import viewsets
from .spotify import get_spotify_token
from .models import Artist, Album, Review
from .serializers import ArtistSerializer, AlbumSerializer, ReviewSerializer

# ==========================
# VIEWSETS API
# ==========================

class ArtistViewSet(viewsets.ModelViewSet):
    queryset = Artist.objects.all()
    serializer_class = ArtistSerializer

class AlbumViewSet(viewsets.ModelViewSet):
    queryset = Album.objects.all()
    serializer_class = AlbumSerializer

class ReviewViewSet(viewsets.ModelViewSet):
    queryset = Review.objects.all()
    serializer_class = ReviewSerializer

# ==========================
# PÁGINAS
# ==========================

def home(request):
    return render(request, 'home.html')

def album_list(request):
    albums = Album.objects.all()
    return render(request, 'albums.html', {'albums': albums})

def test_spotify(request):
    token = get_spotify_token()
    return JsonResponse({"access_token": token})

# ==========================
# SPOTIFY LOGIN
# ==========================

def spotify_login(request):
    auth_url = "https://accounts.spotify.com/authorize"
    params = {
        "client_id": settings.SPOTIFY_CLIENT_ID,
        "response_type": "code",
        "redirect_uri": settings.SPOTIFY_REDIRECT_URI,
        "scope": "user-library-read"
    }
    request_url = requests.Request('GET', auth_url, params=params).prepare().url
    return redirect(request_url)

def spotify_callback(request):
    code = request.GET.get("code")
    if not code:
        return redirect("/")

    token_url = "https://accounts.spotify.com/api/token"
    data = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": settings.SPOTIFY_REDIRECT_URI,
        "client_id": settings.SPOTIFY_CLIENT_ID,
        "client_secret": settings.SPOTIFY_CLIENT_SECRET,
    }

    response = requests.post(token_url, data=data)
    token_info = response.json()
    access_token = token_info.get("access_token")

    if not access_token:
        return redirect("/")

    request.session['spotify_access_token'] = access_token
    request.session.modified = True

    headers = {"Authorization": f"Bearer {access_token}"}

    # Traer TODOS los álbumes guardados con paginación
    all_items = []
    offset = 0
    limit = 50

    while True:
        url = f"https://api.spotify.com/v1/me/albums?limit={limit}&offset={offset}"
        resp = requests.get(url, headers=headers)

        if resp.status_code != 200:
            print("Error Spotify:", resp.status_code, resp.text)
            break

        data = resp.json()
        items = data.get('items', [])
        all_items.extend(items)

        if len(items) < limit:
            break

        offset += limit

    albums_data = {'items': all_items}

    # Guardar en la base de datos
    saved = save_spotify_albums_to_db(albums_data.get('items', []))

    print("Total álbumes traídos:", len(all_items))
    print("Nuevos guardados en DB:", saved)

    # Adaptar datos para el template
    albums_para_mostrar = []

    for item in albums_data.get("items", []):
        album_spotify = item.get("album", {})

        album_adaptado = {
            'title': album_spotify.get('name', 'Sin título'),
            'cover_url': None,
            'release_year': None,
            'artist': {'name': 'Desconocido'}
        }

        if album_spotify.get('images') and len(album_spotify['images']) > 0:
            album_adaptado['cover_url'] = album_spotify['images'][0]['url']

        release_date = album_spotify.get('release_date')
        if release_date and len(release_date) >= 4:
            try:
                album_adaptado['release_year'] = int(release_date[:4])
            except:
                pass

        artists = album_spotify.get('artists', [])
        if artists:
            nombres_artistas = [a.get('name', '') for a in artists]
            album_adaptado['artist']['name'] = ', '.join(nombres_artistas)

        albums_para_mostrar.append(album_adaptado)

    return render(request, "albums.html", {"albums": albums_para_mostrar})

# ==========================
# BÚSQUEDA
# ==========================

def search(request):
    query = request.GET.get('q', '').strip()
    filter_type = request.GET.get('type', 'all')  # 'all', 'album', 'track'

    if not query:
        return render(request, 'search_results.html', {
            'query': '',
            'results': [],
            'count': 0,
            'type': 'none',
            'filter_type': 'all'
        })

    access_token = request.session.get('spotify_access_token')

    if not access_token:
        return render(request, 'search_results.html', {
            'query': query,
            'results': [],
            'count': 0,
            'type': 'not_connected',
            'message': 'Para buscar en Spotify conectá tu cuenta.',
            'filter_type': filter_type
        })

    headers = {"Authorization": f"Bearer {access_token}"}

    # Primero, buscamos el ID del artista (para precisión máxima)
    artist_id = None
    params_artist = {
        'q': query,
        'type': 'artist',
        'limit': 1,
        'market': 'AR'
    }
    response_artist = requests.get("https://api.spotify.com/v1/search", headers=headers, params=params_artist)

    if response_artist.status_code == 200:
        data_artist = response_artist.json()
        artists = data_artist.get('artists', {}).get('items', [])
        if artists and artists[0]['name'].lower() == query.lower():
            artist_id = artists[0]['id']

    results = []

    # Si encontramos el ID del artista, usamos endpoints de discografía/top tracks
    if artist_id:
        if filter_type in ['all', 'album']:
            # Discografía del artista (álbumes, singles, EPs)
            params_albums = {
                'include_groups': 'album,single',  # Incluye álbumes y singles (pero filtramos singles abajo)
                'limit': 10,
                'market': 'AR'
            }
            url_albums = f"https://api.spotify.com/v1/artists/{artist_id}/albums"
            response_albums = requests.get(url_albums, headers=headers, params=params_albums)

            if response_albums.status_code == 200:
                data_albums = response_albums.json()
                albums = data_albums.get('items', [])
                for album in albums:
                    album_type = album.get('album_type', 'unknown')
                    if album_type == 'album':  # Solo álbumes completos (excluimos singles)
                        results.append({
                            'type': 'album',
                            'name': album.get('name'),
                            'artist': ', '.join(a['name'] for a in album.get('artists', [])),
                            'image': album['images'][0]['url'] if album.get('images') else None,
                            'spotify_url': album.get('external_urls', {}).get('spotify')
                        })

        if filter_type in ['all', 'track']:
            # Top tracks del artista
            params_tracks = {
                'market': 'AR'
            }
            url_tracks = f"https://api.spotify.com/v1/artists/{artist_id}/top-tracks"
            response_tracks = requests.get(url_tracks, headers=headers, params=params_tracks)

            if response_tracks.status_code == 200:
                data_tracks = response_tracks.json()
                tracks = data_tracks.get('tracks', [])
                for track in tracks:
                    results.append({
                        'type': 'track',
                        'name': track.get('name'),
                        'artist': ', '.join(a['name'] for a in track.get('artists', [])),
                        'album': track.get('album', {}).get('name'),
                        'image': track['album']['images'][0]['url'] if track.get('album', {}).get('images') else None,
                        'spotify_url': track.get('external_urls', {}).get('spotify')
                    })

    # Si no es un artista, o no encontramos ID, búsqueda general
    else:
        search_types = 'album,track' if filter_type == 'all' else filter_type
        params = {
            'q': query,
            'type': search_types,
            'limit': 10,
            'market': 'AR'
        }
        url = "https://api.spotify.com/v1/search"
        response = requests.get(url, headers=headers, params=params)

        if response.status_code == 200:
            data = response.json()
            if filter_type in ['all', 'album']:
                albums = data.get('albums', {}).get('items', [])
                for album in albums:
                    results.append({
                        'type': 'album',
                        'name': album.get('name'),
                        'artist': ', '.join(a['name'] for a in album.get('artists', [])),
                        'image': album['images'][0]['url'] if album.get('images') else None,
                        'spotify_url': album.get('external_urls', {}).get('spotify')
                    })

            if filter_type in ['all', 'track']:
                tracks = data.get('tracks', {}).get('items', [])
                for track in tracks:
                    results.append({
                        'type': 'track',
                        'name': track.get('name'),
                        'artist': ', '.join(a['name'] for a in track.get('artists', [])),
                        'album': track.get('album', {}).get('name'),
                        'image': track['album']['images'][0]['url'] if track.get('album', {}).get('images') else None,
                        'spotify_url': track.get('external_urls', {}).get('spotify')
                    })

    return render(request, 'search_results.html', {
        'query': query,
        'results': results,
        'count': len(results),
        'type': 'spotify',
        'filter_type': filter_type
    })
# ==========================
# LOGOUT
# ==========================

def spotify_logout(request):
    request.session.pop('spotify_access_token', None)
    return redirect('/')

# ==========================
# GUARDAR EN DB
# ==========================

def save_spotify_albums_to_db(albums_data):
    saved_count = 0

    for item in albums_data:
        spotify_album = item.get("album", {})

        title = spotify_album.get("name")
        artists = spotify_album.get("artists", [])

        if not title or not artists:
            continue

        artist_name = artists[0].get("name")

        artist, _ = Artist.objects.get_or_create(name=artist_name)

        if Album.objects.filter(title=title, artist=artist).exists():
            continue

        release_year = None
        release_date = spotify_album.get("release_date")
        if release_date:
            try:
                release_year = int(release_date[:4])
            except:
                pass

        cover_url = None
        if spotify_album.get("images"):
            cover_url = spotify_album["images"][0]["url"]

        Album.objects.create(
            title=title,
            artist=artist,
            release_year=release_year,
            cover_url=cover_url
        )

        saved_count += 1

    return saved_count