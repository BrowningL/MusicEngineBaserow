"""
Iframe Authentication Endpoints for MusicEngine Integration.

This module supports both:
1. The legacy direct-token iframe bootstrap (`/api/auth/iframe-login/`)
2. The production launch-id bootstrap (`/api/auth/iframe-launch/<launch_id>/`)

The launch-id flow is preferred because it keeps the real Baserow token and
redirect target off the browser-visible iframe URL.
"""

import logging
import os

import requests
from django.http import HttpResponse, HttpResponseBadRequest
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.clickjacking import xframe_options_exempt
from django.utils.decorators import method_decorator
from django.utils.html import escape

from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from rest_framework_simplejwt.tokens import RefreshToken

logger = logging.getLogger(__name__)

MUSICENGINE_APP_URL = os.environ.get('MUSICENGINE_APP_URL', 'https://musicengine.ai').rstrip('/')
IFRAME_LAUNCH_TIMEOUT_SECONDS = float(
    os.environ.get('IFRAME_LAUNCH_REQUEST_TIMEOUT_SECONDS', '5')
)


def sanitize_theme(theme: str) -> str:
    return 'dark' if theme == 'dark' else ('light' if theme == 'light' else '')


def sanitize_redirect_path(redirect_path: str) -> str:
    if not redirect_path.startswith('/'):
        logger.warning("Iframe auth rejected external redirect to %s", redirect_path)
        return '/dashboard'
    return redirect_path


def validate_refresh_token(token: str) -> int | None:
    try:
        validated_token = RefreshToken(token)
        user_id = validated_token.get('user_id')
        if not user_id:
            logger.warning("Iframe login: token missing user_id claim")
            return None
        return user_id
    except (InvalidToken, TokenError) as exc:
        logger.warning("Iframe login: invalid token - %s", exc)
        return None
    except Exception as exc:
        logger.error("Iframe login: unexpected error validating token - %s", exc)
        return None


def build_iframe_bootstrap_html(token: str, redirect_path: str, theme: str) -> str:
    safe_token = escape(token)
    safe_redirect = escape(redirect_path)
    safe_theme = sanitize_theme(theme)

    return f'''<!DOCTYPE html>
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

            // Set theme preference if provided
            if (theme) {{
                localStorage.setItem('isrc-theme', theme);
            }}
        }} catch (e) {{
            // Best-effort only. Cookie auth below can still recover the session.
        }}

        // Set the jwt_token cookie - this is what Baserow's frontend actually reads
        // SameSite=None is required for cross-site iframe embedding
        try {{
            document.cookie = 'jwt_token=' + token + '; path=/; max-age=604800; SameSite=None; Secure';
        }} catch (e) {{
            // Best-effort only. localStorage auth above may already be enough.
        }}

        // Redirect to the target page
        window.location.href = redirect;
    }})();
    </script>
</body>
</html>'''


def build_iframe_bootstrap_response(token: str, redirect_path: str, theme: str):
    if not token:
        logger.warning("Iframe login called without token")
        return HttpResponseBadRequest('Missing token parameter')

    user_id = validate_refresh_token(token)
    if not user_id:
        return HttpResponseBadRequest('Invalid or expired token')

    redirect_path = sanitize_redirect_path(redirect_path)
    safe_theme = sanitize_theme(theme)

    logger.info(
        "Iframe login: injecting token for user_id=%s, theme=%s",
        user_id,
        safe_theme or 'default',
    )

    html = build_iframe_bootstrap_html(token, redirect_path, safe_theme)
    return HttpResponse(html, content_type='text/html')


def redeem_launch_session(launch_id: str):
    try:
        response = requests.post(
            f"{MUSICENGINE_APP_URL}/api/baserow/iframe-launch/{launch_id}",
            headers={'Accept': 'application/json'},
            timeout=IFRAME_LAUNCH_TIMEOUT_SECONDS,
        )
    except requests.RequestException as exc:
        logger.error("Iframe launch redemption request failed - %s", exc)
        return None, HttpResponse('Failed to start workspace session', status=502)

    if response.status_code == 410:
        return None, HttpResponse('Workspace session expired', status=410)

    if response.status_code != 200:
        logger.warning(
            "Iframe launch redemption failed with status=%s for launch_id=%s",
            response.status_code,
            launch_id,
        )
        return None, HttpResponse('Failed to redeem workspace session', status=502)

    try:
        payload = response.json()
    except ValueError:
        logger.error("Iframe launch redemption returned invalid JSON for launch_id=%s", launch_id)
        return None, HttpResponse('Invalid workspace session response', status=502)

    token = payload.get('token')
    redirect_path = payload.get('redirect_path', '/dashboard')
    if not isinstance(token, str) or not token:
        logger.error("Iframe launch redemption missing token for launch_id=%s", launch_id)
        return None, HttpResponse('Invalid workspace session payload', status=502)

    if not isinstance(redirect_path, str) or not redirect_path:
        redirect_path = '/dashboard'

    return {
        'redirect_path': redirect_path,
        'token': token,
    }, None


@method_decorator(csrf_exempt, name='dispatch')
@method_decorator(xframe_options_exempt, name='dispatch')
class IframeLoginView(View):
    def get(self, request):
        token = request.GET.get('token', '')
        redirect_path = request.GET.get('redirect', '/dashboard')
        theme = request.GET.get('theme', '')
        return build_iframe_bootstrap_response(token, redirect_path, theme)


@method_decorator(csrf_exempt, name='dispatch')
@method_decorator(xframe_options_exempt, name='dispatch')
class IframeLaunchView(View):
    def get(self, request, launch_id):
        launch_id = (launch_id or '').strip()
        if not launch_id:
            return HttpResponseBadRequest('Missing launch session')

        payload, error_response = redeem_launch_session(launch_id)
        if error_response is not None:
            return error_response

        return build_iframe_bootstrap_response(
            payload['token'],
            payload['redirect_path'],
            request.GET.get('theme', ''),
        )
