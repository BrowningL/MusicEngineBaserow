from django.urls import path

from .views import SupabaseAuthenticateView, SupabaseHealthView, DevLogoutView
from .iframe_auth import IframeLaunchView, IframeLoginView

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
    # Iframe authentication endpoint for MusicEngine integration
    # Injects JWT token into localStorage and redirects to target page
    path(
        'auth/iframe-login/',
        IframeLoginView.as_view(),
        name='iframe_login'
    ),
    path(
        'auth/iframe-launch/<str:launch_id>/',
        IframeLaunchView.as_view(),
        name='iframe_launch'
    ),
    # DEV ONLY: Logout endpoint - REMOVE BEFORE PRODUCTION
    path(
        'sso/dev-logout/',
        DevLogoutView.as_view(),
        name='dev_logout'
    ),
]
