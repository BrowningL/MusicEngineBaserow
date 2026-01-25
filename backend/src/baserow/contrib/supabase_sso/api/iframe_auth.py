"""
Iframe Authentication Endpoint for ISRCAnalytics Integration

This module provides a token injection endpoint that enables seamless iframe
authentication by:
1. Validating a Baserow JWT token
2. Returning an HTML page that saves the token to localStorage
3. Redirecting to the target Baserow page

This bypasses browser third-party cookie/storage restrictions that prevent
traditional token-based authentication in iframes.
"""

import logging

from django.http import HttpResponse, HttpResponseBadRequest
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.clickjacking import xframe_options_exempt
from django.utils.decorators import method_decorator
from django.utils.html import escape

from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError

logger = logging.getLogger(__name__)


@method_decorator(csrf_exempt, name='dispatch')
@method_decorator(xframe_options_exempt, name='dispatch')
class IframeLoginView(View):
    """
    Token injection endpoint for iframe authentication.

    GET /api/auth/iframe-login/?token=JWT&redirect=/database/123/table/456

    This endpoint:
    1. Validates the provided JWT token
    2. Returns an HTML page with JavaScript that:
       - Saves the JWT to localStorage (where Baserow's Nuxt frontend looks for it)
       - Sets a jwt_token cookie as backup
       - Redirects to the target page

    This works because:
    - The HTML page is served from Baserow's domain (first-party)
    - localStorage writes from first-party pages are not blocked
    - Baserow's frontend sees the token and auto-authenticates
    """

    def get(self, request):
        token = request.GET.get('token', '')
        redirect_path = request.GET.get('redirect', '/dashboard')
        theme = request.GET.get('theme', '')  # Optional: 'light' or 'dark'

        if not token:
            logger.warning("Iframe login called without token")
            return HttpResponseBadRequest('Missing token parameter')

        # Validate the refresh token
        # Baserow stores refresh tokens in the cookie, not access tokens
        try:
            validated_token = RefreshToken(token)
            user_id = validated_token.get('user_id')
            if not user_id:
                logger.warning("Iframe login: token missing user_id claim")
                return HttpResponseBadRequest('Invalid token: missing user_id')
        except (InvalidToken, TokenError) as e:
            logger.warning(f"Iframe login: invalid token - {e}")
            return HttpResponseBadRequest(f'Invalid or expired token')
        except Exception as e:
            logger.error(f"Iframe login: unexpected error validating token - {e}")
            return HttpResponseBadRequest('Token validation error')

        # Sanitize redirect path - only allow internal paths
        if not redirect_path.startswith('/'):
            logger.warning(f"Iframe login: rejected external redirect to {redirect_path}")
            redirect_path = '/dashboard'

        # Escape for safe HTML embedding (prevent XSS)
        safe_token = escape(token)
        safe_redirect = escape(redirect_path)
        # Validate theme - only allow 'light' or 'dark'
        safe_theme = 'dark' if theme == 'dark' else ('light' if theme == 'light' else '')

        logger.info(f"Iframe login: injecting token for user_id={user_id}, redirect={redirect_path}, theme={safe_theme or 'default'}")

        # Return HTML page that injects token into localStorage and redirects
        html = f'''<!DOCTYPE html>
<html>
<head>
    <title>Authenticating...</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            display: flex;
            justify-content: center;
            align-items: center;
            min-height: 100vh;
            margin: 0;
            background: #1a1a2e;
            color: #eee;
        }}
        .container {{
            text-align: center;
            padding: 40px;
        }}
        .spinner {{
            width: 40px;
            height: 40px;
            border: 3px solid rgba(255,255,255,0.3);
            border-radius: 50%;
            border-top-color: #fff;
            animation: spin 1s ease-in-out infinite;
            margin: 0 auto 20px;
        }}
        @keyframes spin {{
            to {{ transform: rotate(360deg); }}
        }}
        p {{
            color: #aaa;
            font-size: 14px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="spinner"></div>
        <p>Authenticating, please wait...</p>
    </div>
    <script>
    (function() {{
        const token = "{safe_token}";
        const redirect = "{safe_redirect}";
        const theme = "{safe_theme}";

        // Save to localStorage - this is where Baserow's Nuxt auth looks for the token
        try {{
            // Primary key used by Baserow
            localStorage.setItem('jwt_token', token);

            // Nuxt auth module also uses these keys
            localStorage.setItem('auth._token.local', 'JWT ' + token);
            localStorage.setItem('auth.strategy', 'local');

            // Legacy keys that some versions may use
            localStorage.setItem('token', token);

            console.log('[IframeAuth] Token saved to localStorage');

            // Set theme preference if provided
            if (theme) {{
                localStorage.setItem('isrc-theme', theme);
                console.log('[IframeAuth] Theme set to:', theme);
            }}
        }} catch (e) {{
            console.warn('[IframeAuth] localStorage not available:', e);
        }}

        // Set the jwt_token cookie - this is what Baserow's frontend actually reads
        // SameSite=None is required for cross-site iframe embedding
        try {{
            document.cookie = 'jwt_token=' + token + '; path=/; max-age=604800; SameSite=None; Secure';
            console.log('[IframeAuth] Token saved to cookie');
        }} catch (e) {{
            console.warn('[IframeAuth] Cookie not available:', e);
        }}

        // Redirect to the target page
        console.log('[IframeAuth] Redirecting to:', redirect);
        window.location.href = redirect;
    }})();
    </script>
</body>
</html>'''

        return HttpResponse(html, content_type='text/html')