from django.urls import path

from .views import SupabaseAuthenticateView, SupabaseHealthView

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
]
