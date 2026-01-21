import logging

from django.apps import AppConfig

logger = logging.getLogger(__name__)


class SupabaseSSOConfig(AppConfig):
    name = 'baserow.contrib.supabase_sso'
    verbose_name = 'Baserow Supabase SSO'

    def ready(self):
        # Import to register the auth provider type
        # Wrapped in try/except to allow Baserow to start even if SSO has issues
        try:
            from . import auth_provider_types  # noqa
            logger.info("Supabase SSO auth provider registered successfully")
        except ImportError as e:
            logger.error(f"Failed to register Supabase SSO auth provider: {e}")
            logger.error("Supabase SSO will not be available. Install PyJWT[crypto]>=2.8.0")
        except Exception as e:
            logger.error(f"Unexpected error registering Supabase SSO: {e}")
