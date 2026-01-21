from rest_framework import serializers


class SupabaseAuthenticateRequestSerializer(serializers.Serializer):
    """
    Serializer for the Supabase SSO authentication request.
    """
    supabase_token = serializers.CharField(
        required=True,
        help_text="The Supabase JWT access token to validate and exchange for Baserow tokens"
    )


class UserSerializer(serializers.Serializer):
    """
    Serializer for basic user info in authentication response.
    """
    id = serializers.IntegerField()
    email = serializers.EmailField()
    first_name = serializers.CharField()
    last_name = serializers.CharField()


class WorkspaceSerializer(serializers.Serializer):
    """
    Serializer for workspace info in authentication response.
    """
    id = serializers.IntegerField()
    name = serializers.CharField()


class SupabaseAuthenticateResponseSerializer(serializers.Serializer):
    """
    Serializer for the Supabase SSO authentication response.
    """
    access_token = serializers.CharField(
        help_text="Baserow JWT access token for API authentication"
    )
    refresh_token = serializers.CharField(
        help_text="Baserow JWT refresh token for getting new access tokens"
    )
    user = UserSerializer(
        help_text="Basic info about the authenticated user"
    )
    workspace = WorkspaceSerializer(
        allow_null=True,
        help_text="User's default workspace (null if none exists)"
    )
    default_database_id = serializers.IntegerField(
        allow_null=True,
        help_text="Default database ID to navigate to"
    )
    default_table_id = serializers.IntegerField(
        allow_null=True,
        help_text="Default table ID to navigate to"
    )
