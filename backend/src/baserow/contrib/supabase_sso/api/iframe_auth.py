"""
Iframe Authentication Endpoints for MusicEngine Integration.

This module supports both:
1. The legacy direct-token iframe bootstrap (`/api/auth/iframe-login/`)
2. The production launch-id bootstrap (`/api/auth/iframe-launch/<launch_id>/`)

The launch-id flow is preferred because it keeps the real Baserow token and
redirect target off the browser-visible iframe URL.
"""

import json
import logging
import os
import re
from urllib.parse import urlparse

import requests
from django.http import HttpResponse, HttpResponseBadRequest
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.clickjacking import xframe_options_exempt
from django.utils.decorators import method_decorator

from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from rest_framework_simplejwt.tokens import RefreshToken

logger = logging.getLogger(__name__)

MUSICENGINE_APP_URL = os.environ.get('MUSICENGINE_APP_URL', 'https://musicengine.ai').rstrip('/')
IFRAME_LAUNCH_TIMEOUT_SECONDS = float(
    os.environ.get('IFRAME_LAUNCH_REQUEST_TIMEOUT_SECONDS', '5')
)
EXTRA_ALLOWED_FRAME_ANCESTORS = os.environ.get(
    'BASEROW_EXTRA_ALLOWED_FRAME_ANCESTORS',
    '',
)


def get_origin(url: str) -> str:
    parsed = urlparse(url)
    if not parsed.scheme or not parsed.netloc:
        return ''
    return f"{parsed.scheme}://{parsed.netloc}"


def get_iframe_allowed_origins() -> list[str]:
    configured_origins = [
        get_origin(MUSICENGINE_APP_URL),
    ]

    for origin in re.split(r'[\s,]+', EXTRA_ALLOWED_FRAME_ANCESTORS.strip()):
        if origin:
            configured_origins.append(origin)

    deduped_origins = []
    for origin in configured_origins:
        cleaned_origin = (origin or '').strip().rstrip('/')
        if not cleaned_origin or cleaned_origin in deduped_origins:
            continue
        deduped_origins.append(cleaned_origin)

    return deduped_origins


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


def build_iframe_bootstrap_html(refresh_token: str, access_token: str | None, redirect_path: str, theme: str) -> str:
    refresh_token_json = json.dumps(refresh_token)
    access_token_json = json.dumps(access_token or '')
    redirect_json = json.dumps(redirect_path)
    theme_json = json.dumps(sanitize_theme(theme))
    app_origins_json = json.dumps(get_iframe_allowed_origins())

    return (
        """<!DOCTYPE html>
<html>
<head>
    <title>Authenticating...</title>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <style>
        html, body {
            margin: 0;
            width: 100%;
            height: 100%;
            background: #ffffff;
        }

        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
        }

        .status {
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 12px;
            min-height: 100vh;
            color: #334155;
            font-size: 14px;
        }

        .spinner {
            width: 18px;
            height: 18px;
            border: 2px solid rgba(51, 65, 85, 0.18);
            border-top-color: rgba(51, 65, 85, 0.72);
            border-radius: 50%;
            animation: spin 0.9s linear infinite;
        }

        iframe {
            display: block;
            width: 100%;
            height: 100%;
            border: 0;
            background: #ffffff;
        }

        @keyframes spin {
            to { transform: rotate(360deg); }
        }
    </style>
</head>
<body>
    <div class="status" id="bootstrap-status">
        <div class="spinner"></div>
        <span>Authenticating, please wait...</span>
    </div>
    <script>
    (function() {
        var refreshToken = __REFRESH_TOKEN__;
        var apiToken = __ACCESS_TOKEN__ || refreshToken;
        var redirectPath = __REDIRECT_PATH__;
        var theme = __THEME__;
        var trustedAppOrigins = __TRUSTED_APP_ORIGINS__;

        function persistSession() {
            localStorage.setItem('jwt_token', refreshToken);
            localStorage.setItem('refresh_token', refreshToken);
            localStorage.setItem('auth.strategy', 'local');
            if (apiToken) {
                localStorage.setItem('auth._token.local', 'JWT ' + apiToken);
                localStorage.setItem('token', apiToken);
            }

            if (theme) {
                localStorage.setItem('isrc-theme', theme);
            }

            document.cookie = 'jwt_token=' + encodeURIComponent(refreshToken) +
                '; path=/; max-age=604800; SameSite=None; Secure';
        }

        function shouldAttachMusicEngineAuth(url, origin) {
            try {
                var parsed = new URL(url, origin);

                if (trustedAppOrigins.indexOf(parsed.origin) === -1) {
                    return false;
                }

                if (parsed.pathname.indexOf('/api/catalogue/') === 0) {
                    return true;
                }

                if (
                    parsed.pathname === '/api/playlists/slots' ||
                    parsed.pathname.indexOf('/api/playlists/slots/') === 0
                ) {
                    return true;
                }

                if (
                    parsed.pathname === '/api/baserow/trigger-inspiration-download' ||
                    parsed.pathname.indexOf('/api/baserow/trigger-inspiration-download/') === 0
                ) {
                    return true;
                }

                return false;
            } catch (e) {
                return false;
            }
        }

        function withAuthorizationHeader(headersSource) {
            var headers = new Headers(headersSource || {});
            if (!headers.has('Authorization') && apiToken) {
                headers.set('Authorization', 'Bearer ' + apiToken);
            }
            return headers;
        }

        function patchNetwork(win) {
            if (!win || win.__musicengineIframeNetworkPatched) {
                return;
            }

            win.__musicengineIframeNetworkPatched = true;

            var origin = win.location && win.location.origin
                ? win.location.origin
                : window.location.origin;

            if (typeof win.fetch === 'function') {
                var originalFetch = win.fetch.bind(win);
                win.fetch = function (input, init) {
                    var url = '';
                    if (typeof input === 'string') {
                        url = input;
                    } else if (input && typeof input === 'object' && input.url) {
                        url = input.url;
                    }

                    if (apiToken && shouldAttachMusicEngineAuth(url, origin)) {
                        var nextInit = init ? Object.assign({}, init) : {};
                        var nextHeaders = withAuthorizationHeader(
                            nextInit.headers ||
                            (input && typeof input === 'object' && input.headers ? input.headers : undefined)
                        );
                        nextInit.headers = nextHeaders;

                        if (input && typeof input === 'object' && input.url) {
                            return originalFetch(new win.Request(input, nextInit));
                        }

                        return originalFetch(input, nextInit);
                    }

                    return originalFetch(input, init);
                };
            }

            if (typeof win.XMLHttpRequest === 'function') {
                var OriginalXHR = win.XMLHttpRequest;

                function WrappedXHR() {
                    var xhr = new OriginalXHR();
                    var url = '';
                    var hasAuthorizationHeader = false;

                    var originalOpen = xhr.open;
                    xhr.open = function (method, nextUrl) {
                        url = nextUrl || '';
                        return originalOpen.apply(xhr, arguments);
                    };

                    var originalSetRequestHeader = xhr.setRequestHeader;
                    xhr.setRequestHeader = function (header, value) {
                        if (String(header || '').toLowerCase() === 'authorization') {
                            hasAuthorizationHeader = true;
                        }
                        return originalSetRequestHeader.apply(xhr, arguments);
                    };

                    var originalSend = xhr.send;
                    xhr.send = function () {
                        if (apiToken && !hasAuthorizationHeader && shouldAttachMusicEngineAuth(url, origin)) {
                            try {
                                originalSetRequestHeader.call(xhr, 'Authorization', 'Bearer ' + apiToken);
                            } catch (e) {
                                // Best effort.
                            }
                        }
                        return originalSend.apply(xhr, arguments);
                    };

                    return xhr;
                }

                WrappedXHR.UNSENT = OriginalXHR.UNSENT;
                WrappedXHR.OPENED = OriginalXHR.OPENED;
                WrappedXHR.HEADERS_RECEIVED = OriginalXHR.HEADERS_RECEIVED;
                WrappedXHR.LOADING = OriginalXHR.LOADING;
                WrappedXHR.DONE = OriginalXHR.DONE;
                WrappedXHR.prototype = OriginalXHR.prototype;

                win.XMLHttpRequest = WrappedXHR;
            }
        }

        function syncTokenToFrame(frameEl, nextToken) {
            if (!frameEl || !frameEl.contentWindow || !nextToken) {
                return;
            }
            try {
                frameEl.contentWindow.postMessage({
                    type: 'BASEROW_TOKEN_UPDATE',
                    token: nextToken
                }, '*');
            } catch (e) {
                // Best effort.
            }
        }

        function wireMessageBridge(frameEl) {
            if (!frameEl || window.__musicengineIframeBridgeAttached) {
                return;
            }

            window.__musicengineIframeBridgeAttached = true;

            window.addEventListener('message', function (event) {
                var data = event.data || {};

                if (event.source === frameEl.contentWindow) {
                    if (data.type === 'BASEROW_REFRESH_REQUEST' || data.type === 'BASEROW_SESSION_DEAD') {
                        try {
                            window.parent.postMessage(data, '*');
                        } catch (e) {
                            // Best effort.
                        }
                    }
                    return;
                }

                if (event.source !== window.parent) {
                    return;
                }

                if (data.type === 'BASEROW_TOKEN_UPDATE' && data.token) {
                    apiToken = data.token;
                    try {
                        localStorage.setItem('auth._token.local', 'JWT ' + apiToken);
                        localStorage.setItem('token', apiToken);
                    } catch (e) {
                        // Best effort.
                    }
                    syncTokenToFrame(frameEl, data.token);
                    return;
                }

                if (data.type === 'BASEROW_SESSION_DEAD') {
                    try {
                        frameEl.contentWindow && frameEl.contentWindow.postMessage(data, '*');
                    } catch (e) {
                        // Best effort.
                    }
                }
            });
        }

        function mountWorkspaceFrame() {
            document.body.innerHTML =
                '<iframe id="musicengine-workspace-frame" title="Baserow Workspace"></iframe>';

            var frame = document.getElementById('musicengine-workspace-frame');
            if (!frame) {
                window.location.href = redirectPath;
                return;
            }

            wireMessageBridge(frame);

            var initializeFrame = function () {
                try {
                    patchNetwork(frame.contentWindow);
                    syncTokenToFrame(frame, apiToken);
                } catch (e) {
                    // Best effort.
                }
            };

            frame.addEventListener('load', initializeFrame);
            frame.src = redirectPath;
            setTimeout(initializeFrame, 500);
        }

        try {
            persistSession();
        } catch (e) {
            document.body.innerHTML = '<div class="status">Authentication failed.</div>';
            return;
        }

        mountWorkspaceFrame();
    })();
    </script>
</body>
    )
        </html>"""
        .replace('__REFRESH_TOKEN__', refresh_token_json)
        .replace('__ACCESS_TOKEN__', access_token_json)
        .replace('__REDIRECT_PATH__', redirect_json)
        .replace('__THEME__', theme_json)
        .replace('__TRUSTED_APP_ORIGINS__', app_origins_json)
    )


def build_iframe_bootstrap_response(refresh_token: str, access_token: str | None, redirect_path: str, theme: str):
    if not refresh_token:
        logger.warning("Iframe login called without token")
        return HttpResponseBadRequest('Missing token parameter')

    user_id = validate_refresh_token(refresh_token)
    if not user_id:
        return HttpResponseBadRequest('Invalid or expired token')

    redirect_path = sanitize_redirect_path(redirect_path)
    safe_theme = sanitize_theme(theme)

    logger.info(
        "Iframe login: injecting token for user_id=%s, theme=%s",
        user_id,
        safe_theme or 'default',
    )

    html = build_iframe_bootstrap_html(refresh_token, access_token, redirect_path, safe_theme)
    response = HttpResponse(html, content_type='text/html')
    response.set_cookie(
        'jwt_token',
        refresh_token,
        max_age=604800,
        httponly=False,
        secure=True,
        samesite='None',
        path='/',
    )

    allowed_origins = get_iframe_allowed_origins()
    if allowed_origins:
        response['Content-Security-Policy'] = f"frame-ancestors {' '.join(allowed_origins)}"
    response['X-Frame-Options'] = 'ALLOWALL'
    return response


def redeem_launch_session(launch_id: str):
    try:
        response = requests.post(
            f"{MUSICENGINE_APP_URL}/api/baserow/iframe-launch/{launch_id}",
            headers={'Accept': 'application/json'},
            timeout=IFRAME_LAUNCH_TIMEOUT_SECONDS,
            allow_redirects=False,
        )
    except requests.RequestException as exc:
        logger.error("Iframe launch redemption request failed - %s", exc)
        return None, HttpResponse('Failed to start workspace session', status=502)

    if 300 <= response.status_code < 400:
        logger.warning(
            "Iframe launch redemption was redirected with status=%s for launch_id=%s to location=%s",
            response.status_code,
            launch_id,
            response.headers.get('Location'),
        )
        return None, HttpResponse('Failed to redeem workspace session', status=502)

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

    access_token = payload.get('access_token')
    redirect_path = payload.get('redirect_path', '/dashboard')
    refresh_token = payload.get('refresh_token') or payload.get('token')
    if not isinstance(refresh_token, str) or not refresh_token:
        logger.error("Iframe launch redemption missing token for launch_id=%s", launch_id)
        return None, HttpResponse('Invalid workspace session payload', status=502)

    if not isinstance(redirect_path, str) or not redirect_path:
        redirect_path = '/dashboard'

    return {
        'access_token': access_token if isinstance(access_token, str) and access_token else None,
        'redirect_path': redirect_path,
        'refresh_token': refresh_token,
    }, None


@method_decorator(csrf_exempt, name='dispatch')
@method_decorator(xframe_options_exempt, name='dispatch')
class IframeLoginView(View):
    def get(self, request):
        refresh_token = request.GET.get('token', '')
        access_token = request.GET.get('access_token', '')
        redirect_path = request.GET.get('redirect', '/dashboard')
        theme = request.GET.get('theme', '')
        return build_iframe_bootstrap_response(refresh_token, access_token, redirect_path, theme)


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
            payload.get('refresh_token', ''),
            payload.get('access_token'),
            payload['redirect_path'],
            request.GET.get('theme', ''),
        )
