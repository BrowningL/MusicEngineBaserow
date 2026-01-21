from django.apps import AppConfig


class SupabaseSSOConfig(AppConfig):
    name = 'baserow.contrib.supabase_sso'
    verbose_name = 'Baserow Supabase SSO'

    def ready(self):
        # Import to register the auth provider type
        from . import auth_provider_types  # noqa
