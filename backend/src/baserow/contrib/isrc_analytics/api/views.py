"""
API views for ISRC Analytics - adds enriched tracks/playlists to Baserow tables.
Enrichment is handled by the ISRCAnalytics.com frontend calling Spotify directly.
"""

import logging

from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from baserow.api.decorators import validate_body

from ..handler import (
    DatabaseNotFoundError,
    IsrcHandler,
    IsrcHandlerException,
    TableNotFoundError,
)
from .serializers import (
    ErrorSerializer,
    PlaylistAddRequestSerializer,
    PlaylistAddResponseSerializer,
    TrackAddRequestSerializer,
    TrackAddResponseSerializer,
)

logger = logging.getLogger(__name__)


class AddTrackView(APIView):
    """Add an enriched track to the user's catalogue."""

    permission_classes = (IsAuthenticated,)

    @extend_schema(
        tags=["ISRC Analytics"],
        operation_id="add_track",
        description="Add an enriched track to the user's Live Catalogue Tracks table",
        request=TrackAddRequestSerializer,
        responses={
            201: TrackAddResponseSerializer,
            400: ErrorSerializer,
            404: ErrorSerializer,
            500: ErrorSerializer,
        },
    )
    @validate_body(TrackAddRequestSerializer)
    def post(self, request, data):
        try:
            # Add track to user's table
            handler = IsrcHandler()
            result = handler.add_track(request.user, data)

            return Response(result, status=status.HTTP_201_CREATED)

        except DatabaseNotFoundError as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_404_NOT_FOUND,
            )
        except TableNotFoundError as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_404_NOT_FOUND,
            )
        except IsrcHandlerException as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except Exception as e:
            logger.exception(f"Error adding track: {e}")
            return Response(
                {"error": "Failed to add track", "detail": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class AddPlaylistView(APIView):
    """Add an enriched playlist to the user's playlists."""

    permission_classes = (IsAuthenticated,)

    @extend_schema(
        tags=["ISRC Analytics"],
        operation_id="add_playlist",
        description="Add an enriched playlist to the user's Live Catalogue Playlists table",
        request=PlaylistAddRequestSerializer,
        responses={
            201: PlaylistAddResponseSerializer,
            400: ErrorSerializer,
            404: ErrorSerializer,
            500: ErrorSerializer,
        },
    )
    @validate_body(PlaylistAddRequestSerializer)
    def post(self, request, data):
        try:
            # Add playlist to user's table
            handler = IsrcHandler()
            result = handler.add_playlist(request.user, data)

            return Response(result, status=status.HTTP_201_CREATED)

        except DatabaseNotFoundError as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_404_NOT_FOUND,
            )
        except TableNotFoundError as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_404_NOT_FOUND,
            )
        except IsrcHandlerException as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except Exception as e:
            logger.exception(f"Error adding playlist: {e}")
            return Response(
                {"error": "Failed to add playlist", "detail": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
