from django.urls import path

from .views import SupabaseAuthenticateView, SupabaseHealthView, DevLogoutView

app_name = 'supabase_sso'

urlpatterns = [
    path(
        'sso/supabase/authenticate/',
        SupabaseAuthenticateView.as_view(),
        name='authenticate'
    ),
    path(
        'sso/supabase/health/',
        SupabaseHealthView.as_view(),
        name='health'
    ),
    # DEV ONLY: Logout endpoint - REMOVE BEFORE PRODUCTION
    path(
        'sso/dev-logout/',
        DevLogoutView.as_view(),
        name='dev_logout'
    ),
]
