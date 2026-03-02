from django.http import JsonResponse
from django.test import RequestFactory, TestCase
from unittest.mock import patch
from .views import search


class SearchViewTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()

    @patch('core.views.render', side_effect=lambda request, template, context: JsonResponse(context))
    @patch('core.views.requests.get')
    def test_search_album_uses_playlist_type(self, mock_get, _mock_render):
        request = self.factory.get('/search', {'q': 'Bad Bunny', 'type': 'album'})

        mock_get.return_value = _mock_response({'items': [
            {'id': {'playlistId': 'pl1'}, 'snippet': {'title': 'Oasis', 'channelTitle': 'Bad Bunny', 'thumbnails': {}}}
        ]})

        response = search(request)
        payload = response.json()

        first_call = mock_get.call_args_list[0]
        self.assertEqual(first_call.kwargs['params']['type'], 'playlist')
        self.assertEqual(payload['count'], 1)

    @patch('core.views.render', side_effect=lambda request, template, context: JsonResponse(context))
    @patch('core.views.requests.get')
    def test_album_only_fallback_uses_artist_qualified_query(self, mock_get, _mock_render):
        request = self.factory.get('/search', {'q': 'Bad Bunny', 'type': 'track'})

        mock_get.return_value = _mock_response({'items': [
            {'id': {'videoId': 'v1'}, 'snippet': {'title': 'Track 1', 'channelTitle': 'Bad Bunny', 'thumbnails': {}}}
        ]})

        response = search(request)
        payload = response.json()

        first_call = mock_get.call_args_list[0]
        self.assertEqual(first_call.kwargs['params']['type'], 'video')
        self.assertEqual(payload['count'], 1)


def _mock_response(payload, status=200):
    class MockResponse:
        status_code = status

        def json(self):
            return payload

    return MockResponse()