"""
API serializers for ISRC Analytics - adding tracks/playlists to Baserow tables.
"""

from rest_framework import serializers


class TrackAddRequestSerializer(serializers.Serializer):
    """Request serializer for adding a track to the catalogue."""

    title = serializers.CharField()
    artist = serializers.CharField()
    isrc = serializers.CharField()
    album = serializers.CharField(allow_blank=True, required=False, allow_null=True)
    spotify_track_url = serializers.CharField(required=False, allow_null=True)
    spotify_uri = serializers.CharField(required=False, allow_null=True)
    spotify_track_id = serializers.CharField(required=False, allow_null=True)
    spotify_album_id = serializers.CharField(required=False, allow_null=True)
    upc = serializers.CharField(allow_blank=True, required=False, allow_null=True)
    release_date = serializers.CharField(allow_blank=True, required=False, allow_null=True)
    duration_ms = serializers.IntegerField(required=False, allow_null=True)
    cover_url = serializers.CharField(required=False, allow_null=True)
    label = serializers.CharField(allow_blank=True, required=False, allow_null=True)
    copyright_c = serializers.CharField(allow_blank=True, required=False, allow_null=True)
    copyright_p = serializers.CharField(allow_blank=True, required=False, allow_null=True)


class TrackAddResponseSerializer(serializers.Serializer):
    """Response serializer for track add operation."""

    success = serializers.BooleanField()
    track_id = serializers.CharField(allow_null=True)
    row_id = serializers.IntegerField(allow_null=True)
    message = serializers.CharField(allow_blank=True)


class PlaylistAddRequestSerializer(serializers.Serializer):
    """Request serializer for adding a playlist."""

    playlist_name = serializers.CharField()
    playlist_uri = serializers.CharField()
    owner_uri = serializers.CharField(required=False, allow_null=True)
    owner_name = serializers.CharField(allow_blank=True, required=False, allow_null=True)
    cover_url = serializers.CharField(required=False, allow_null=True)
    playlist_web_url = serializers.CharField(required=False, allow_null=True)


class PlaylistAddResponseSerializer(serializers.Serializer):
    """Response serializer for playlist add operation."""

    success = serializers.BooleanField()
    playlist_id = serializers.CharField(allow_null=True)
    row_id = serializers.IntegerField(allow_null=True)
    message = serializers.CharField(allow_blank=True)


class ErrorSerializer(serializers.Serializer):
    """Generic error response serializer."""

    error = serializers.CharField()
    detail = serializers.CharField(required=False, allow_blank=True)
