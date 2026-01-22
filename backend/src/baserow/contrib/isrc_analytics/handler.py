"""
Handler for ISRC Analytics operations.
Manages track and playlist insertion into Baserow tables.
"""

import logging
import uuid
from typing import Any, Dict, Tuple

from django.contrib.auth import get_user_model

from baserow.contrib.database.fields.models import Field
from baserow.contrib.database.models import Database
from baserow.contrib.database.rows.handler import RowHandler
from baserow.contrib.database.table.models import Table

User = get_user_model()
logger = logging.getLogger(__name__)


class IsrcHandlerException(Exception):
    """Base exception for ISRC handler errors."""

    pass


class DatabaseNotFoundError(IsrcHandlerException):
    """Raised when Live Catalogue database is not found."""

    pass


class TableNotFoundError(IsrcHandlerException):
    """Raised when a required table is not found."""

    pass


class IsrcHandler:
    """Handler for ISRC Analytics track and playlist operations."""

    LIVE_CATALOGUE_DB_NAME = "Live Catalogue"
    TRACKS_TABLE_NAME = "Tracks"
    PLAYLISTS_TABLE_NAME = "Playlists"

    def get_user_workspace(self, user: User):
        """Get the user's primary workspace."""
        workspace_user = user.workspaceuser_set.first()
        if not workspace_user:
            raise IsrcHandlerException("User has no workspace")
        return workspace_user.workspace

    def get_live_catalogue_database(self, user: User) -> Database:
        """Get the Live Catalogue database for a user."""
        workspace = self.get_user_workspace(user)

        try:
            database = Database.objects.get(
                name=self.LIVE_CATALOGUE_DB_NAME,
                workspace=workspace,
                trashed=False,
            )
            return database
        except Database.DoesNotExist:
            raise DatabaseNotFoundError(
                f"Database '{self.LIVE_CATALOGUE_DB_NAME}' not found in workspace"
            )

    def get_table(self, database: Database, table_name: str) -> Table:
        """Get a table by name within a database."""
        try:
            table = Table.objects.get(
                name=table_name,
                database=database,
                trashed=False,
            )
            return table
        except Table.DoesNotExist:
            raise TableNotFoundError(
                f"Table '{table_name}' not found in database '{database.name}'"
            )

    def get_field_mapping(self, table: Table) -> Dict[str, int]:
        """Get a mapping of field names to field IDs for a table."""
        fields = Field.objects.filter(table=table)
        return {field.name: field.id for field in fields}

    def get_tracks_table(self, user: User) -> Tuple[Table, Dict[str, int]]:
        """Get the Tracks table and its field mapping for a user."""
        database = self.get_live_catalogue_database(user)
        table = self.get_table(database, self.TRACKS_TABLE_NAME)
        field_mapping = self.get_field_mapping(table)
        return table, field_mapping

    def get_playlists_table(self, user: User) -> Tuple[Table, Dict[str, int]]:
        """Get the Playlists table and its field mapping for a user."""
        database = self.get_live_catalogue_database(user)
        table = self.get_table(database, self.PLAYLISTS_TABLE_NAME)
        field_mapping = self.get_field_mapping(table)
        return table, field_mapping

    def add_track(self, user: User, track_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Add a track to the user's Tracks table.

        Args:
            user: The authenticated user
            track_data: Dict with track fields (title, artist, isrc, etc.)

        Returns:
            Dict with success status, track_id, and row_id
        """
        table, field_mapping = self.get_tracks_table(user)

        # Generate a unique track_id
        track_id = str(uuid.uuid4())

        # Map track data to field values using field IDs
        field_name_to_value = {
            "track_id": track_id,
            "isrc": track_data.get("isrc"),
            "title": track_data.get("title"),
            "artist": track_data.get("artist"),
            "album": track_data.get("album"),
            "release_date": track_data.get("release_date"),
            "duration_ms": track_data.get("duration_ms"),
            "cover_url": track_data.get("cover_url"),
            "spotify_track_url": track_data.get("spotify_track_url"),
            "spotify_track_id": track_data.get("spotify_track_id"),
            "spotify_uri": track_data.get("spotify_uri"),
            "upc": track_data.get("upc"),
            "label": track_data.get("label"),
            "copyright_c": track_data.get("copyright_c"),
            "copyright_p": track_data.get("copyright_p"),
        }

        values = {}
        for field_name, value in field_name_to_value.items():
            if field_name in field_mapping and value is not None:
                values[f"field_{field_mapping[field_name]}"] = value

        # Get the table model and create the row
        model = table.get_model()
        row_handler = RowHandler()
        row = row_handler.create_row(
            user=user,
            table=table,
            values=values,
            model=model,
            user_field_names=False,
        )

        logger.info(f"Added track {track_id} (row {row.id}) for user {user.email}")

        return {
            "success": True,
            "track_id": track_id,
            "row_id": row.id,
            "message": "Track added successfully",
        }

    def add_playlist(self, user: User, playlist_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Add a playlist to the user's Playlists table.

        Args:
            user: The authenticated user
            playlist_data: Dict with playlist fields (playlist_name, playlist_uri, etc.)

        Returns:
            Dict with success status, playlist_id, and row_id
        """
        table, field_mapping = self.get_playlists_table(user)

        # Generate a unique playlist_id
        playlist_id = str(uuid.uuid4())

        # Map playlist data to field values using field IDs
        field_name_to_value = {
            "playlist_id": playlist_id,
            "playlist_name": playlist_data.get("playlist_name"),
            "playlist_uri": playlist_data.get("playlist_uri"),
            "owner_uri": playlist_data.get("owner_uri"),
            "owner_name": playlist_data.get("owner_name"),
            "cover_url": playlist_data.get("cover_url"),
            "playlist_web_url": playlist_data.get("playlist_web_url"),
        }

        values = {}
        for field_name, value in field_name_to_value.items():
            if field_name in field_mapping and value is not None:
                values[f"field_{field_mapping[field_name]}"] = value

        # Get the table model and create the row
        model = table.get_model()
        row_handler = RowHandler()
        row = row_handler.create_row(
            user=user,
            table=table,
            values=values,
            model=model,
            user_field_names=False,
        )

        logger.info(f"Added playlist {playlist_id} (row {row.id}) for user {user.email}")

        return {
            "success": True,
            "playlist_id": playlist_id,
            "row_id": row.id,
            "message": "Playlist added successfully",
        }
