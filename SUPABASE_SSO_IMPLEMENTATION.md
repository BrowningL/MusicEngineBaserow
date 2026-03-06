# Supabase SSO Integration for MusicEngine Baserow Fork

## Overview

This document outlines the implementation plan for integrating Supabase authentication with Baserow, enabling seamless single sign-on (SSO) for MusicEngine users.

## Goals

1. Users authenticated via Supabase can access Baserow without separate login
2. Auto-provision Baserow user + workspace on first access
3. No Baserow passwords needed - Supabase JWT is the only credential
4. Seamless iframe embedding in MusicEngine.ai

## Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                         AUTHENTICATION FLOW                          │
└─────────────────────────────────────────────────────────────────────┘

1. User logs into MusicEngine.ai (Supabase Auth)
   └─> User has Supabase JWT in cookies/localStorage

2. User visits /workspace page
   └─> MusicEngine frontend gets Supabase access_token

3. Frontend calls: POST /api/baserow/sso-exchange
   └─> Body: { supabase_token: "..." }
   └─> MusicEngine backend validates token, calls Baserow SSO endpoint

4. Baserow SSO endpoint: POST /api/sso/supabase/authenticate/
   └─> Validates Supabase JWT using JWKS
   └─> Extracts user_id, email, name from claims
   └─> Gets or creates Baserow user (keyed by supabase_user_id)
   └─> Auto-provisions workspace if new user
   └─> Returns Baserow JWT tokens

5. MusicEngine returns Baserow tokens to frontend
   └─> Frontend loads iframe with Baserow JWT

6. Baserow iframe authenticates via JWT cookie
   └─> User sees their workspace (no login screen)
```

## Implementation Details

### Phase 1: Backend - Supabase Auth Provider

#### 1.1 Create Supabase Auth Provider Model

**File:** `backend/src/baserow/contrib/supabase_sso/models.py`

```python
from django.db import models
from baserow.core.auth_provider.models import AuthProviderModel


class SupabaseAuthProviderModel(AuthProviderModel):
    """
    Stores Supabase configuration for SSO authentication.
    """
    supabase_url = models.URLField(
        help_text="Supabase project URL (e.g., https://xxx.supabase.co)"
    )
    supabase_anon_key = models.CharField(
        max_length=512,
        help_text="Supabase anon/public key"
    )
    jwks_url = models.URLField(
        blank=True,
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

    def get_jwks_url(self):
        if self.jwks_url:
            return self.jwks_url
        return f"{self.supabase_url.rstrip('/')}/auth/v1/.well-known/jwks.json"
```

#### 1.2 Create User-Supabase Mapping Model

**File:** `backend/src/baserow/contrib/supabase_sso/models.py` (continued)

```python
class SupabaseUserMapping(models.Model):
    """
    Maps Supabase user IDs to Baserow users.
    This is the source of truth for user identity.
    """
    user = models.OneToOneField(
        'auth.User',
        on_delete=models.CASCADE,
        related_name='supabase_mapping'
    )
    supabase_user_id = models.CharField(
        max_length=255,
        unique=True,
        db_index=True,
        help_text="Supabase user UUID"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    last_login_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Supabase User Mapping"
        verbose_name_plural = "Supabase User Mappings"
```

#### 1.3 Create Supabase Auth Provider Type

**File:** `backend/src/baserow/contrib/supabase_sso/auth_provider_types.py`

```python
import jwt
import requests
from jwt import PyJWKClient
from typing import Optional, Tuple
from django.contrib.auth import get_user_model

from baserow.core.auth_provider.auth_provider_types import AuthProviderType
from baserow.core.auth_provider.registries import auth_provider_type_registry
from baserow.core.user.handler import UserHandler
from baserow.core.handler import CoreHandler
from .models import SupabaseAuthProviderModel, SupabaseUserMapping

User = get_user_model()


class SupabaseAuthProviderType(AuthProviderType):
    type = "supabase"
    model_class = SupabaseAuthProviderModel
    allowed_fields = [
        "supabase_url",
        "supabase_anon_key",
        "jwks_url",
        "auto_provision_workspace",
        "template_workspace_id",
    ]
    serializer_field_names = allowed_fields

    def validate_supabase_jwt(
        self,
        token: str,
        auth_provider: SupabaseAuthProviderModel
    ) -> Optional[dict]:
        """
        Validate a Supabase JWT and return the claims if valid.
        """
        try:
            jwks_url = auth_provider.get_jwks_url()
            jwks_client = PyJWKClient(jwks_url)
            signing_key = jwks_client.get_signing_key_from_jwt(token)

            claims = jwt.decode(
                token,
                signing_key.key,
                algorithms=["RS256"],
                audience="authenticated",
                options={"verify_exp": True}
            )
            return claims
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None
        except Exception:
            return None

    def get_or_create_user(
        self,
        auth_provider: SupabaseAuthProviderModel,
        supabase_user_id: str,
        email: str,
        name: str,
    ) -> Tuple[User, bool]:
        """
        Get existing user by Supabase ID or create new one.
        Returns (user, created_bool).
        """
        # Try to find existing mapping
        try:
            mapping = SupabaseUserMapping.objects.select_related('user').get(
                supabase_user_id=supabase_user_id
            )
            # Update last login
            mapping.save(update_fields=['last_login_at'])
            return mapping.user, False
        except SupabaseUserMapping.DoesNotExist:
            pass

        # Check if user with this email exists (migration case)
        try:
            existing_user = User.objects.get(email=email)
            # Create mapping for existing user
            SupabaseUserMapping.objects.create(
                user=existing_user,
                supabase_user_id=supabase_user_id
            )
            return existing_user, False
        except User.DoesNotExist:
            pass

        # Create new user
        user_handler = UserHandler()

        # Split name into first/last
        name_parts = name.split(' ', 1) if name else ['User', '']
        first_name = name_parts[0]
        last_name = name_parts[1] if len(name_parts) > 1 else ''

        user = user_handler.create_user(
            name=name or email.split('@')[0],
            email=email,
            password=None,  # No password for SSO users
            language='en',
        )

        # Create Supabase mapping
        SupabaseUserMapping.objects.create(
            user=user,
            supabase_user_id=supabase_user_id
        )

        # Auto-provision workspace if enabled
        if auth_provider.auto_provision_workspace:
            self._provision_workspace(user, auth_provider, name)

        return user, True

    def _provision_workspace(
        self,
        user: User,
        auth_provider: SupabaseAuthProviderModel,
        name: str
    ):
        """
        Create workspace for new user and duplicate templates.
        """
        core_handler = CoreHandler()

        # Create workspace
        workspace_name = f"{name}'s Workspace" if name else f"Workspace"
        workspace = core_handler.create_workspace(user=user, name=workspace_name)

        # Duplicate templates if configured
        if auth_provider.template_workspace_id:
            # TODO: Implement template duplication
            # This would copy databases from template workspace to user's workspace
            pass

        return workspace

    def authenticate(
        self,
        auth_provider: SupabaseAuthProviderModel,
        supabase_token: str
    ) -> Optional[User]:
        """
        Validate Supabase token and return authenticated user.
        """
        claims = self.validate_supabase_jwt(supabase_token, auth_provider)
        if not claims:
            return None

        supabase_user_id = claims.get('sub')
        email = claims.get('email')
        name = claims.get('user_metadata', {}).get('full_name', '')

        if not supabase_user_id or not email:
            return None

        user, created = self.get_or_create_user(
            auth_provider=auth_provider,
            supabase_user_id=supabase_user_id,
            email=email,
            name=name,
        )

        return user


# Register the provider type
auth_provider_type_registry.register(SupabaseAuthProviderType())
```

#### 1.4 Create API Views

**File:** `backend/src/baserow/contrib/supabase_sso/api/views.py`

```python
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny

from baserow.core.user.utils import generate_session_tokens_for_user
from baserow.core.auth_provider.registries import auth_provider_type_registry
from ..models import SupabaseAuthProviderModel


class SupabaseAuthenticateView(APIView):
    """
    Authenticate a user using their Supabase JWT token.
    Returns Baserow JWT tokens if successful.
    """
    permission_classes = [AllowAny]

    def post(self, request):
        supabase_token = request.data.get('supabase_token')

        if not supabase_token:
            return Response(
                {'error': 'supabase_token is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Get the Supabase auth provider (assuming single provider for now)
        try:
            auth_provider = SupabaseAuthProviderModel.objects.get(enabled=True)
        except SupabaseAuthProviderModel.DoesNotExist:
            return Response(
                {'error': 'Supabase SSO is not configured'},
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )

        # Authenticate
        provider_type = auth_provider_type_registry.get('supabase')
        user = provider_type.authenticate(auth_provider, supabase_token)

        if not user:
            return Response(
                {'error': 'Invalid or expired Supabase token'},
                status=status.HTTP_401_UNAUTHORIZED
            )

        if not user.is_active:
            return Response(
                {'error': 'User account is deactivated'},
                status=status.HTTP_403_FORBIDDEN
            )

        # Generate Baserow tokens
        tokens = generate_session_tokens_for_user(
            user,
            include_refresh_token=True
        )

        # Get user's default workspace info
        workspaces = list(user.workspace_set.all()[:1])
        default_workspace = workspaces[0] if workspaces else None

        return Response({
            'access_token': tokens['access_token'],
            'refresh_token': tokens['refresh_token'],
            'user': {
                'id': user.id,
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
            },
            'workspace': {
                'id': default_workspace.id,
                'name': default_workspace.name,
            } if default_workspace else None
        })
```

#### 1.5 Register URLs

**File:** `backend/src/baserow/contrib/supabase_sso/api/urls.py`

```python
from django.urls import path
from .views import SupabaseAuthenticateView

app_name = 'supabase_sso'

urlpatterns = [
    path(
        'sso/supabase/authenticate/',
        SupabaseAuthenticateView.as_view(),
        name='authenticate'
    ),
]
```

#### 1.6 Create Django App Configuration

**File:** `backend/src/baserow/contrib/supabase_sso/apps.py`

```python
from django.apps import AppConfig


class SupabaseSSOConfig(AppConfig):
    name = 'baserow.contrib.supabase_sso'
    verbose_name = 'Baserow Supabase SSO'

    def ready(self):
        # Import to register the auth provider type
        from . import auth_provider_types  # noqa
```

#### 1.7 Database Migrations

Create migration for the new models:

```bash
cd backend
python manage.py makemigrations supabase_sso
python manage.py migrate
```

### Phase 2: Frontend Updates (Minimal)

Since we're embedding Baserow in an iframe, the frontend changes are minimal. The main change is to accept JWT tokens via URL parameters for auto-login.

#### 2.1 Update Token Handling

**File:** `web-frontend/modules/core/plugins/clientAuthRefresh.js`

Add support for accepting tokens via URL parameter (already partially exists for `?token=`):

```javascript
// Check for token in URL (for iframe embedding)
const urlToken = new URL(window.location.href).searchParams.get('token')
if (urlToken) {
  // Set token in store and cookies
  await store.dispatch('auth/setToken', urlToken)
  // Remove token from URL for security
  const url = new URL(window.location.href)
  url.searchParams.delete('token')
  window.history.replaceState({}, '', url.toString())
}
```

### Phase 3: MusicEngine.ai Updates

#### 3.1 Simplified Workspace URL API

**File:** `app/api/baserow/workspace-url/route.ts`

```typescript
import { NextResponse } from 'next/server';
import { createClient } from '@/lib/supabase/server';

export const dynamic = 'force-dynamic';

const BASEROW_API_URL = process.env.BASEROW_API_URL;
const BASEROW_URL = process.env.BASEROW_PUBLIC_URL;

export async function GET() {
  try {
    const supabase = createClient();

    // Get Supabase session
    const { data: { session }, error: authError } = await supabase.auth.getSession();

    if (authError || !session) {
      return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
    }

    // Exchange Supabase token for Baserow token
    const response = await fetch(`${BASEROW_API_URL}/sso/supabase/authenticate/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        supabase_token: session.access_token
      }),
    });

    if (!response.ok) {
      const error = await response.json();
      return NextResponse.json(
        { error: error.error || 'Authentication failed' },
        { status: response.status }
      );
    }

    const data = await response.json();

    // Build iframe URL
    const iframeUrl = data.workspace
      ? `${BASEROW_URL}/database/${data.workspace.id}?token=${data.refresh_token}`
      : `${BASEROW_URL}/dashboard?token=${data.refresh_token}`;

    return NextResponse.json({
      workspace_id: data.workspace?.id,
      workspace_name: data.workspace?.name,
      jwt_token: data.access_token,
      refresh_token: data.refresh_token,
      iframe_url: iframeUrl,
    });
  } catch (error) {
    console.error('Workspace URL API error:', error);
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    );
  }
}
```

### Phase 4: Configuration

#### 4.1 Environment Variables

**Baserow:**
```env
# Supabase SSO Configuration
SUPABASE_SSO_ENABLED=true
SUPABASE_URL=https://kdbvecdosgiaaotzrwmb.supabase.co
SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
SUPABASE_TEMPLATE_WORKSPACE_ID=133
```

**MusicEngine.ai:**
```env
# Simplified - no more admin credentials needed
BASEROW_API_URL=https://baserow-app-production.up.railway.app/api
BASEROW_PUBLIC_URL=https://baserow-app-production.up.railway.app
```

#### 4.2 Database Setup

After deploying the fork, create the Supabase auth provider via Django admin or API:

```python
# Via Django shell
from baserow.contrib.supabase_sso.models import SupabaseAuthProviderModel

SupabaseAuthProviderModel.objects.create(
    enabled=True,
    name='Supabase SSO',
    supabase_url='https://kdbvecdosgiaaotzrwmb.supabase.co',
    supabase_anon_key='eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...',
    auto_provision_workspace=True,
    template_workspace_id=133,
)
```

## File Structure

```
backend/src/baserow/contrib/supabase_sso/
├── __init__.py
├── apps.py
├── models.py
├── auth_provider_types.py
├── api/
│   ├── __init__.py
│   ├── urls.py
│   ├── views.py
│   └── serializers.py
└── migrations/
    └── 0001_initial.py
```

## Testing Checklist

- [ ] New user: Supabase JWT creates Baserow user + workspace
- [ ] Existing user: Supabase JWT returns existing user's workspace
- [ ] Invalid token: Returns 401
- [ ] Expired token: Returns 401
- [ ] User deactivated: Returns 403
- [ ] Template duplication works for new users
- [ ] Iframe embedding works with JWT parameter
- [ ] Token refresh works in embedded iframe

## Migration Plan

1. Deploy forked Baserow with Supabase SSO
2. Create Supabase auth provider record
3. Update MusicEngine.ai to use new SSO endpoint
4. Migrate existing users by creating SupabaseUserMapping records
5. Remove old password-based code

## Security Considerations

1. **Token Validation:** Always validate Supabase JWT using JWKS (not shared secret)
2. **Token Expiry:** Respect token expiration, don't cache indefinitely
3. **HTTPS Only:** All token exchanges must be over HTTPS
4. **No Token Logging:** Never log JWT tokens in production
5. **Rate Limiting:** Apply rate limits to authentication endpoint
