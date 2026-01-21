import logging

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
from drf_spectacular.utils import extend_schema

from baserow.core.user.utils import generate_session_tokens_for_user
from baserow.core.registries import auth_provider_type_registry
from baserow.contrib.database.models import Database, Table

from ..models import SupabaseAuthProviderModel
from .serializers import (
    SupabaseAuthenticateRequestSerializer,
    SupabaseAuthenticateResponseSerializer,
)

logger = logging.getLogger(__name__)


class SupabaseAuthenticateView(APIView):
    """
    Authenticate a user using their Supabase JWT token.

    This endpoint validates the Supabase JWT, provisions a Baserow user
    if needed, and returns Baserow JWT tokens for subsequent API access.

    This is the core SSO endpoint for ISRCAnalytics integration.
    """
    permission_classes = [AllowAny]

    @extend_schema(
        tags=["SSO"],
        operation_id="supabase_authenticate",
        description=(
            "Exchange a Supabase JWT access token for Baserow JWT tokens. "
            "If the user doesn't exist in Baserow, they will be automatically "
            "provisioned with a workspace."
        ),
        request=SupabaseAuthenticateRequestSerializer,
        responses={
            200: SupabaseAuthenticateResponseSerializer,
            400: None,
            401: None,
            403: None,
            503: None,
        },
    )
    def post(self, request):
        # Validate request
        serializer = SupabaseAuthenticateRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {'error': 'supabase_token is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        supabase_token = serializer.validated_data['supabase_token']

        # Get the enabled Supabase auth provider
        try:
            auth_provider = SupabaseAuthProviderModel.objects.get(enabled=True)
        except SupabaseAuthProviderModel.DoesNotExist:
            logger.error("No enabled Supabase SSO provider found")
            return Response(
                {'error': 'Supabase SSO is not configured'},
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )
        except SupabaseAuthProviderModel.MultipleObjectsReturned:
            # If multiple enabled providers, use the first one
            auth_provider = SupabaseAuthProviderModel.objects.filter(enabled=True).first()

        # Authenticate using the provider
        try:
            provider_type = auth_provider_type_registry.get('supabase')
        except Exception:
            logger.error("Supabase auth provider type not registered")
            return Response(
                {'error': 'Supabase SSO is not configured'},
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )

        logger.info(f"SSO authenticate called with token length={len(supabase_token)}, provider={auth_provider.supabase_url}")
        user = provider_type.authenticate(auth_provider, supabase_token)

        if not user:
            logger.error(f"SSO authentication returned None - token validation failed")
            return Response(
                {'error': 'Invalid or expired Supabase token'},
                status=status.HTTP_401_UNAUTHORIZED
            )

        if not user.is_active:
            logger.warning(f"Supabase authentication failed - user {user.id} is deactivated")
            return Response(
                {'error': 'User account is deactivated'},
                status=status.HTTP_403_FORBIDDEN
            )

        # Generate Baserow tokens
        tokens = generate_session_tokens_for_user(
            user,
            include_refresh_token=True
        )

        # Get user's default workspace and navigation info
        workspace_info = None
        default_database_id = None
        default_table_id = None

        workspaces = list(user.workspace_set.all()[:1])
        if workspaces:
            workspace = workspaces[0]
            workspace_info = {
                'id': workspace.id,
                'name': workspace.name,
            }

            # Find default database and table for navigation
            # Prefer "Live Catalogue" if it exists
            databases = Database.objects.filter(workspace_id=workspace.id)
            live_catalogue = databases.filter(name__icontains='Live Catalogue').first()
            default_db = live_catalogue or databases.first()

            if default_db:
                default_database_id = default_db.id
                # Get first table in the database
                tables = Table.objects.filter(database_id=default_db.id)
                tracks_table = tables.filter(name='Tracks').first()
                default_table = tracks_table or tables.first()
                if default_table:
                    default_table_id = default_table.id

        logger.info(f"Supabase authentication successful for user {user.id}")

        return Response({
            'access_token': tokens['access_token'],
            'refresh_token': tokens['refresh_token'],
            'user': {
                'id': user.id,
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
            },
            'workspace': workspace_info,
            'default_database_id': default_database_id,
            'default_table_id': default_table_id,
        })


class SupabaseHealthView(APIView):
    """
    Health check endpoint for Supabase SSO configuration.
    """
    permission_classes = [AllowAny]

    @extend_schema(
        tags=["SSO"],
        operation_id="supabase_health",
        description="Check if Supabase SSO is configured and enabled.",
        responses={
            200: None,
            503: None,
        },
    )
    def get(self, request):
        try:
            provider = SupabaseAuthProviderModel.objects.get(enabled=True)
            return Response({
                'status': 'ok',
                'provider_id': provider.id,
                'supabase_url': provider.supabase_url,
                'auto_provision_workspace': provider.auto_provision_workspace,
                'template_workspace_id': provider.template_workspace_id,
            })
        except SupabaseAuthProviderModel.DoesNotExist:
            return Response(
                {'status': 'not_configured'},
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )


class DevLogoutView(APIView):
    """
    DEV ONLY: Simple logout page that clears localStorage tokens.
    REMOVE THIS BEFORE PRODUCTION DEPLOYMENT.
    """
    permission_classes = [AllowAny]

    def get(self, request):
        # Return an HTML page that clears localStorage and optionally logs in as admin
        html = '''
<!DOCTYPE html>
<html>
<head>
    <title>Dev Login Manager</title>
    <style>
        body { font-family: sans-serif; display: flex; justify-content: center; align-items: center; min-height: 100vh; margin: 0; background: #f5f5f5; }
        .container { text-align: center; background: white; padding: 40px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); max-width: 500px; }
        h1 { color: #333; margin-bottom: 10px; }
        p { color: #666; margin-bottom: 20px; }
        .status { padding: 10px; border-radius: 4px; margin: 10px 0; }
        .success { background: #d4edda; color: #155724; }
        .error { background: #f8d7da; color: #721c24; }
        .info { background: #d1ecf1; color: #0c5460; }
        button { padding: 12px 24px; margin: 5px; border: none; border-radius: 4px; cursor: pointer; font-size: 14px; }
        .btn-logout { background: #dc3545; color: white; }
        .btn-admin { background: #28a745; color: white; }
        .btn-logout:hover { background: #c82333; }
        .btn-admin:hover { background: #218838; }
        input { width: 100%; padding: 10px; margin: 5px 0; border: 1px solid #ddd; border-radius: 4px; box-sizing: border-box; }
        .form-group { text-align: left; margin: 15px 0; }
        label { display: block; margin-bottom: 5px; color: #333; }
        hr { margin: 20px 0; border: none; border-top: 1px solid #eee; }
    </style>
</head>
<body>
    <div class="container">
        <h1>Dev Login Manager</h1>
        <p>Manage your Baserow session for development</p>

        <div id="status" class="status info">Choose an action below</div>

        <button class="btn-logout" onclick="logout()">Clear Session (Logout)</button>
        <button class="btn-admin" onclick="loginAsAdmin()">Login as Admin</button>

        <hr>

        <h3>Or login with custom credentials:</h3>
        <div class="form-group">
            <label>Email:</label>
            <input type="email" id="email" placeholder="admin@isrcanalytics.com">
        </div>
        <div class="form-group">
            <label>Password:</label>
            <input type="password" id="password" placeholder="Password">
        </div>
        <button class="btn-admin" onclick="loginCustom()">Login</button>
    </div>

    <script>
        function setStatus(message, type) {
            const status = document.getElementById('status');
            status.textContent = message;
            status.className = 'status ' + type;
        }

        function logout() {
            setStatus('Clearing session...', 'info');

            // Clear all Baserow tokens from localStorage
            localStorage.removeItem('jwt_token');
            localStorage.removeItem('refresh_token');
            localStorage.removeItem('token');

            // Clear any other auth-related items
            for (let key of Object.keys(localStorage)) {
                if (key.includes('token') || key.includes('auth') || key.includes('user')) {
                    localStorage.removeItem(key);
                }
            }

            // Clear sessionStorage too
            sessionStorage.clear();

            setStatus('Session cleared! You are now logged out.', 'success');
        }

        async function loginAsAdmin() {
            await doLogin('admin@isrcanalytics.com', 'AdminPass123!');
        }

        async function loginCustom() {
            const email = document.getElementById('email').value;
            const password = document.getElementById('password').value;
            if (!email || !password) {
                setStatus('Please enter email and password', 'error');
                return;
            }
            await doLogin(email, password);
        }

        async function doLogin(email, password) {
            setStatus('Logging in...', 'info');

            // First clear existing session
            logout();

            try {
                const response = await fetch('/api/user/token-auth/', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ email, password })
                });

                if (!response.ok) {
                    const error = await response.json();
                    setStatus('Login failed: ' + (error.error || error.detail || 'Invalid credentials'), 'error');
                    return;
                }

                const data = await response.json();

                // Store tokens in localStorage (Baserow format)
                localStorage.setItem('jwt_token', data.access_token || data.token);
                if (data.refresh_token) {
                    localStorage.setItem('refresh_token', data.refresh_token);
                }

                // Also try the 'token' key that some Baserow versions use
                localStorage.setItem('token', data.access_token || data.token);

                setStatus('Login successful! Redirecting to dashboard...', 'success');

                // Redirect to dashboard after a moment
                setTimeout(() => {
                    window.location.href = '/dashboard';
                }, 1500);

            } catch (err) {
                setStatus('Login error: ' + err.message, 'error');
            }
        }
    </script>
</body>
</html>
'''
        from django.http import HttpResponse
        return HttpResponse(html, content_type='text/html')
