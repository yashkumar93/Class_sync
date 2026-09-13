"""Allow the Android WebView to authenticate existing HTML views with its JWT."""
from rest_framework_simplejwt.authentication import JWTAuthentication


class JwtWebViewAuthenticationMiddleware:
    """Populate request.user from an Authorization header when no session exists.

    DRF performs this for API views itself. This middleware deliberately only
    fills an anonymous request so normal Django session authentication remains
    authoritative for browser users.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if not request.user.is_authenticated:
            try:
                result = JWTAuthentication().authenticate(request)
                if result:
                    request.user, request.auth = result
            except Exception:
                # Invalid mobile credentials should behave exactly like an
                # anonymous web request rather than breaking the page.
                pass
        return self.get_response(request)
