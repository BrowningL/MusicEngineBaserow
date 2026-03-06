"""
URL configuration for MusicEngine API endpoints.
Only handles adding tracks/playlists to Baserow tables.
Enrichment is done via MusicEngine.ai API.
"""

from django.urls import re_path

from .views import AddPlaylistView, AddTrackView

app_name = "baserow.contrib.isrc_analytics.api"

urlpatterns = [
    re_path(
        r"^catalogue/add/$",
        AddTrackView.as_view(),
        name="add_track",
    ),
    re_path(
        r"^playlists/add/$",
        AddPlaylistView.as_view(),
        name="add_playlist",
    ),
]
