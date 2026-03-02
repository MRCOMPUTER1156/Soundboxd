import requests
from django.conf import settings
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login
from django.contrib.auth.forms import UserCreationForm
from django.http import JsonResponse
from datetime import datetime


# ==========================
# DJANGO VIEWS (YouTube)
# ==========================


def home(request):
    return render(request, 'home.html')


def signup(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('home')
    else:
        form = UserCreationForm()
    return render(request, 'signup.html', {'form': form})


def search(request):
    query = request.GET.get('q', '').strip()
    sort = request.GET.get('sort', 'popular')  # popular, alpha_asc, alpha_desc, newest, oldest
    results = []

    if query:
        params = {'q': query, 'part': 'snippet', 'maxResults': 25, 'type': 'video,playlist'}

        api_key = getattr(settings, 'YOUTUBE_API_KEY', None)
        if api_key:
            params['key'] = api_key

        try:
            resp = requests.get('https://www.googleapis.com/youtube/v3/search', params=params, timeout=8)
            data = resp.json()
            items = data.get('items', [])

            # Collect video IDs to fetch statistics for ranking
            video_ids = [it.get('id', {}).get('videoId') for it in items if it.get('id', {}).get('videoId')]

            stats_map = {}
            if video_ids and api_key:
                vids_params = {'part': 'statistics', 'id': ','.join(video_ids), 'key': api_key}
                vids_resp = requests.get('https://www.googleapis.com/youtube/v3/videos', params=vids_params, timeout=8)
                vids_data = vids_resp.json()
                for vi in vids_data.get('items', []):
                    vid = vi.get('id')
                    stats = vi.get('statistics', {})
                    try:
                        view_count = int(stats.get('viewCount', 0))
                    except (TypeError, ValueError):
                        view_count = 0
                    stats_map[vid] = {'viewCount': view_count}

            # import models here to avoid circular import at module load
            from .models import Video, Rating
            from django.db.models import Avg

            for it in items:
                snippet = it.get('snippet', {})
                title = snippet.get('title')
                channel = snippet.get('channelTitle')
                thumb = (snippet.get('thumbnails') or {}).get('high', {}).get('url')
                idinfo = it.get('id', {})
                published = snippet.get('publishedAt')
                published_dt = None
                if published:
                    try:
                        published_dt = datetime.fromisoformat(published.replace('Z', '+00:00'))
                    except Exception:
                        published_dt = None

                if 'videoId' in idinfo:
                    vid = idinfo.get('videoId')
                    youtube_url = f'https://www.youtube.com/watch?v={vid}'
                    item_type = 'track'
                    views = stats_map.get(vid, {}).get('viewCount', 0)

                    # check DB for ratings
                    try:
                        video_obj = Video.objects.filter(video_id=vid).first()
                        avg_rating = None
                        user_rating = None
                        if video_obj:
                            avg = Rating.objects.filter(video=video_obj).aggregate(Avg('rating'))['rating__avg']
                            if avg is not None:
                                avg_rating = round(avg, 2)
                            if request.user.is_authenticated:
                                ur = Rating.objects.filter(video=video_obj, user=request.user).first()
                                if ur:
                                    user_rating = ur.rating
                        else:
                            avg_rating = None
                            user_rating = None
                    except Exception:
                        avg_rating = None
                        user_rating = None

                elif 'playlistId' in idinfo:
                    youtube_url = f'https://www.youtube.com/playlist?list={idinfo["playlistId"]}'
                    item_type = 'album'
                    vid = None
                    views = 0
                    avg_rating = None
                    user_rating = None
                else:
                    youtube_url = None
                    item_type = 'track'
                    vid = None
                    views = 0
                    avg_rating = None
                    user_rating = None

                results.append({
                    'type': item_type,
                    'name': title,
                    'artist': channel or '',
                    'image': thumb,
                    'youtube_url': youtube_url,
                    'views': views,
                    'video_id': vid,
                    'published_at': published_dt,
                    'avg_rating': avg_rating,
                    'user_rating': user_rating,
                })

            # Sorting
            if sort == 'alpha_asc':
                results.sort(key=lambda x: (x.get('name') or '').lower())
            elif sort == 'alpha_desc':
                results.sort(key=lambda x: (x.get('name') or '').lower(), reverse=True)
            elif sort == 'newest':
                results.sort(key=lambda x: x.get('published_at') or datetime.min, reverse=True)
            elif sort == 'oldest':
                results.sort(key=lambda x: x.get('published_at') or datetime.max)
            else:  # popular
                results.sort(key=lambda x: x.get('views', 0), reverse=True)

        except Exception:
            pass

    count = len(results)
    return render(request, 'search_results.html', {
        'query': query,
        'results': results,
        'count': count,
        'sort': sort,
        'type': 'youtube',
    })


@login_required
def rate_video(request):
    if request.method != 'POST':
        return JsonResponse({'ok': False, 'error': 'POST required'}, status=400)

    video_id = request.POST.get('video_id')
    try:
        rating_val = int(request.POST.get('rating', 0))
    except Exception:
        rating_val = 0

    if not video_id or rating_val < 1 or rating_val > 5:
        return JsonResponse({'ok': False, 'error': 'Invalid data'}, status=400)

    from .models import Video, Rating
    video_obj, _ = Video.objects.get_or_create(video_id=video_id, defaults={'title': request.POST.get('title', '') , 'channel': request.POST.get('channel',''), 'thumbnail': request.POST.get('thumbnail','')})

    rating_obj, created = Rating.objects.update_or_create(user=request.user, video=video_obj, defaults={'rating': rating_val})

    # calculate new average
    from django.db.models import Avg
    avg = Rating.objects.filter(video=video_obj).aggregate(Avg('rating'))['rating__avg']
    return JsonResponse({'ok': True, 'avg': round(avg, 2) if avg is not None else None})
