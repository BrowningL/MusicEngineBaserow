from django.db import models
from django.conf import settings

from baserow.core.auth_provider.models import AuthProviderModel


class SupabaseAuthProviderModel(AuthProviderModel):
    """
    Stores Supabase configuration for SSO authentication.
    Allows MusicEngine users to authenticate to Baserow using their Supabase JWT.
    """
    supabase_url = models.URLField(
        help_text="Supabase project URL (e.g., https://xxx.supabase.co)"
    )
    supabase_anon_key = models.CharField(
        max_length=512,
        help_text="Supabase anon/public key for API access"
    )
    jwks_url = models.URLField(
        blank=True,
        default='',
        help_text="JWKS URL for JWT validation. Defaults to {supabase_url}/auth/v1/.well-known/jwks.json"
    )
    auto_provision_workspace = models.BooleanField(
        default=True,
        help_text="Automatically create workspace for new users"
    )
    template_workspace_id = models.IntegerField(
        null=True,
        blank=True,
        help_text="Workspace ID to duplicate templates from for new users"
    )
    default_workspace_name_template = models.CharField(
        max_length=255,
        default="{name}'s Workspace",
        help_text="Template for new workspace names. Use {name} for user's name."
    )

    class Meta:
        verbose_name = "Supabase Auth Provider"
        verbose_name_plural = "Supabase Auth Providers"

    def get_jwks_url(self):
        """Get the JWKS URL for JWT validation."""
        if self.jwks_url:
            return self.jwks_url
        return f"{self.supabase_url.rstrip('/')}/auth/v1/.well-known/jwks.json"

    def __str__(self):
        return f"Supabase SSO ({self.supabase_url})"


class SupabaseUserMapping(models.Model):
    """
    Maps Supabase user IDs to Baserow users.
    This is the source of truth for user identity - one Supabase user = one Baserow user.
    """
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='supabase_mapping'
    )
    supabase_user_id = models.CharField(
        max_length=255,
        unique=True,
        db_index=True,
        help_text="Supabase user UUID (sub claim from JWT)"
    )
    supabase_email = models.EmailField(
        help_text="Email from Supabase (for reference/debugging)"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    last_login_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Supabase User Mapping"
        verbose_name_plural = "Supabase User Mappings"

    def __str__(self):
        return f"{self.supabase_email} -> User #{self.user_id}"
