from .base import *  # noqa: F401, F403

DEBUG = False

# Set explicitly via environment — never wildcard in production.
# ALLOWED_HOSTS is already read from env in base.py.

# CORS_ALLOWED_ORIGINS must be set via environment — no localhost.
# Override here so a misconfigured prod env fails loudly.
CORS_ALLOWED_ORIGINS = []
CORS_ALLOWED_ORIGIN_REGEXES = []

# --- Security headers ---
SECURE_SSL_REDIRECT = True
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = "DENY"
